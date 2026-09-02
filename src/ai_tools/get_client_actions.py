"""Ferramenta autorizada: consulta ações (leads, compras, mensagens...)
de um cliente num período.

Substitui a antiga `get_client_conversions.py` — a tabela `conversions`
não existe mais neste schema (decisão do projeto: Sync não duplica
dado de lead/CRM, só métricas agregadas de campanha). Esta ferramenta
lê de `daily_actions`, sempre filtrando por `action_type_catalog.
is_canonical = true` para não contar o mesmo evento sob nomes
diferentes (ver docs/meta-ads-api-exploracao.md).

Uso:

python -m src.ai_tools.get_client_actions --client seed-cliente-teste --start 2026-08-01 --end 2026-08-31

A ferramenta aceita somente parâmetros de negócio.
Não existe parâmetro para SQL arbitrário.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from src.ai_tools.db import fetch_all, fetch_one, get_connection


def _json_default(value: Any) -> Any:
    """Converte tipos do Postgres para JSON."""

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, Decimal):
        return float(value)

    raise TypeError(
        f"Tipo não serializável: {type(value).__name__}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Consulta ações canônicas (lead, purchase, message...) de um cliente do Sync."
    )

    parser.add_argument(
        "--client",
        required=True,
        help="Slug exato do cliente.",
    )

    parser.add_argument(
        "--start",
        required=True,
        help="Data inicial no formato YYYY-MM-DD.",
    )

    parser.add_argument(
        "--end",
        required=True,
        help="Data final no formato YYYY-MM-DD.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    client_slug = args.client.strip()

    if not client_slug:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "O slug do cliente não pode ser vazio.",
                },
                ensure_ascii=False,
            )
        )
        return 2

    try:
        start_date = date.fromisoformat(args.start)
        end_date = date.fromisoformat(args.end)
    except ValueError:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "As datas devem estar no formato YYYY-MM-DD.",
                },
                ensure_ascii=False,
            )
        )
        return 2

    if start_date > end_date:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "A data inicial não pode ser maior que a data final.",
                },
                ensure_ascii=False,
            )
        )
        return 2

    client_query = """
        SELECT
            id,
            name,
            slug,
            industry,
            status
        FROM clients
        WHERE slug = %s
        LIMIT 1
    """

    # Resumo por categoria de negócio, só ações canônicas. LEFT JOIN a
    # partir do catálogo garante que toda categoria apareça mesmo com
    # zero eventos no período (evita a lista sumir silenciosamente).
    summary_query = """
        SELECT
            action_type_catalog.business_category,
            COALESCE(SUM(daily_actions.count), 0) AS total_count,
            COALESCE(SUM(daily_actions.value), 0) AS total_value

        FROM action_type_catalog

        LEFT JOIN daily_actions
            ON daily_actions.action_type = action_type_catalog.action_type
            AND daily_actions.ad_group_id IS NULL
            AND daily_actions.ad_id IS NULL
            AND daily_actions.metric_date BETWEEN %s AND %s
            AND daily_actions.campaign_id IN (
                SELECT campaigns.id
                FROM campaigns
                INNER JOIN ad_accounts ON ad_accounts.id = campaigns.ad_account_id
                INNER JOIN clients ON clients.id = ad_accounts.client_id
                WHERE clients.slug = %s
            )

        WHERE action_type_catalog.is_canonical = true

        GROUP BY action_type_catalog.business_category
        ORDER BY action_type_catalog.business_category
    """

    # Detalhe por campanha, só categorias com algum evento no período.
    by_campaign_query = """
        SELECT
            campaigns.id AS campaign_id,
            campaigns.name AS campaign_name,
            action_type_catalog.business_category,
            SUM(daily_actions.count) AS total_count,
            SUM(daily_actions.value) AS total_value

        FROM daily_actions

        INNER JOIN action_type_catalog
            ON action_type_catalog.action_type = daily_actions.action_type

        INNER JOIN campaigns
            ON campaigns.id = daily_actions.campaign_id

        INNER JOIN ad_accounts
            ON ad_accounts.id = campaigns.ad_account_id

        INNER JOIN clients
            ON clients.id = ad_accounts.client_id

        WHERE clients.slug = %s
          AND action_type_catalog.is_canonical = true
          AND daily_actions.ad_group_id IS NULL
          AND daily_actions.ad_id IS NULL
          AND daily_actions.metric_date BETWEEN %s AND %s

        GROUP BY campaigns.id, campaigns.name, action_type_catalog.business_category
        ORDER BY campaigns.id, action_type_catalog.business_category
    """

    try:
        with get_connection() as connection:
            client = fetch_one(
                connection,
                client_query,
                (client_slug,),
            )

            if client is None:
                print(
                    json.dumps(
                        {
                            "ok": False,
                            "error": "Cliente não encontrado.",
                            "client_slug": client_slug,
                        },
                        ensure_ascii=False,
                    )
                )
                return 3

            summary_rows = fetch_all(
                connection,
                summary_query,
                (start_date, end_date, client_slug),
            )

            by_campaign_rows = fetch_all(
                connection,
                by_campaign_query,
                (client_slug, start_date, end_date),
            )

    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "Falha ao consultar as ações do cliente.",
                    "details": str(exc),
                },
                ensure_ascii=False,
            )
        )
        return 1

    by_category = {
        row["business_category"]: {
            "count": float(row["total_count"] or 0),
            "value": float(row["total_value"] or 0),
        }
        for row in summary_rows
    }

    by_campaign = [
        {
            "campaign_id": row["campaign_id"],
            "campaign_name": row["campaign_name"],
            "business_category": row["business_category"],
            "count": float(row["total_count"] or 0),
            "value": float(row["total_value"] or 0),
        }
        for row in by_campaign_rows
    ]

    print(
        json.dumps(
            {
                "ok": True,
                "client": client,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "note": (
                    "Contagens vêm apenas de action_type marcados is_canonical=true "
                    "no action_type_catalog, para não somar o mesmo evento sob "
                    "nomes diferentes."
                ),
                "summary_by_category": by_category,
                "by_campaign": by_campaign,
            },
            ensure_ascii=False,
            default=_json_default,
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
