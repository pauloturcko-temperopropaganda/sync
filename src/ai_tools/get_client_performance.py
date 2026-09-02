"""Ferramenta autorizada: consulta desempenho agregado de TODAS as
campanhas de um cliente num período (visão de conta/cliente, não de
uma campanha isolada).

Uso:

python -m src.ai_tools.get_client_performance --client seed-cliente-teste --start 2026-08-01 --end 2026-08-05

A ferramenta aceita parâmetros de negócio.
Não existe parâmetro para SQL arbitrário.

Para ações (leads, compras, mensagens...) do cliente, usar
`get_client_actions` — este script cobre só as métricas de
`daily_metrics` (impressões, cliques, investimento, alcance).

Mesma regra de grão de `get_campaign_performance`: soma apenas
linhas com ad_group_id/ad_id/device/publisher_platform nulos, para
não contar a mesma métrica duas vezes quando existir dado mais
granular para a mesma campanha/data.
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
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    raise TypeError(f"Tipo não serializável: {type(value).__name__}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Consulta o desempenho agregado de todas as campanhas de um cliente."
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
                {"ok": False, "error": "O slug do cliente não pode ser vazio."},
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
                {"ok": False, "error": "As datas devem estar no formato YYYY-MM-DD."},
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
        SELECT id, name, slug, industry, status
        FROM clients
        WHERE slug = %s
        LIMIT 1
    """

    # Agregado geral (uma linha só, mesmo se o cliente não tiver
    # nenhuma campanha ou nenhuma métrica no período).
    summary_query = """
        SELECT
            COALESCE(SUM(daily_metrics.impressions), 0) AS impressions,
            COALESCE(SUM(daily_metrics.clicks), 0) AS clicks,
            COALESCE(SUM(daily_metrics.spend), 0) AS spend,
            COALESCE(SUM(daily_metrics.reach), 0) AS reach_daily_sum

        FROM campaigns

        INNER JOIN ad_accounts
            ON ad_accounts.id = campaigns.ad_account_id

        INNER JOIN clients
            ON clients.id = ad_accounts.client_id

        LEFT JOIN daily_metrics
            ON daily_metrics.campaign_id = campaigns.id
            AND daily_metrics.metric_date BETWEEN %s AND %s
            AND daily_metrics.ad_group_id IS NULL
            AND daily_metrics.ad_id IS NULL
            AND daily_metrics.device IS NULL
            AND daily_metrics.publisher_platform IS NULL

        WHERE clients.slug = %s
    """

    # Quebra por campanha, ordenada por investimento (maior primeiro).
    # LEFT JOIN também aqui: campanha sem métrica no período aparece
    # com zero, não some da lista.
    by_campaign_query = """
        SELECT
            campaigns.id AS campaign_id,
            campaigns.name AS campaign_name,
            campaigns.status,
            COALESCE(SUM(daily_metrics.impressions), 0) AS impressions,
            COALESCE(SUM(daily_metrics.clicks), 0) AS clicks,
            COALESCE(SUM(daily_metrics.spend), 0) AS spend

        FROM campaigns

        INNER JOIN ad_accounts
            ON ad_accounts.id = campaigns.ad_account_id

        INNER JOIN clients
            ON clients.id = ad_accounts.client_id

        LEFT JOIN daily_metrics
            ON daily_metrics.campaign_id = campaigns.id
            AND daily_metrics.metric_date BETWEEN %s AND %s
            AND daily_metrics.ad_group_id IS NULL
            AND daily_metrics.ad_id IS NULL
            AND daily_metrics.device IS NULL
            AND daily_metrics.publisher_platform IS NULL

        WHERE clients.slug = %s

        GROUP BY campaigns.id, campaigns.name, campaigns.status
        ORDER BY spend DESC
    """

    try:
        with get_connection() as connection:
            client = fetch_one(connection, client_query, (client_slug,))

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

            summary_row = fetch_one(
                connection,
                summary_query,
                (start_date, end_date, client_slug),
            )

            by_campaign_rows = fetch_all(
                connection,
                by_campaign_query,
                (start_date, end_date, client_slug),
            )

    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "Falha ao consultar o desempenho do cliente.",
                    "details": str(exc),
                },
                ensure_ascii=False,
            )
        )
        return 1

    impressions = int(summary_row["impressions"] or 0)
    clicks = int(summary_row["clicks"] or 0)
    spend = float(summary_row["spend"] or 0)

    ctr = (clicks / impressions * 100) if impressions else 0
    cpc = (spend / clicks) if clicks else 0
    cpm = (spend / impressions * 1000) if impressions else 0

    summary = {
        "impressions": impressions,
        "clicks": clicks,
        "spend": round(spend, 2),
        "reach_daily_sum": int(summary_row["reach_daily_sum"] or 0),
        "reach_daily_sum_note": (
            "Soma do alcance diário, não é alcance único do período — "
            "o mesmo usuário pode ser contado em mais de um dia."
        ),
        "ctr_percent": round(ctr, 2),
        "cpc": round(cpc, 2),
        "cpm": round(cpm, 2),
    }

    by_campaign = [
        {
            "campaign_id": row["campaign_id"],
            "campaign_name": row["campaign_name"],
            "status": row["status"],
            "impressions": int(row["impressions"] or 0),
            "clicks": int(row["clicks"] or 0),
            "spend": round(float(row["spend"] or 0), 2),
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
                "summary": summary,
                "by_campaign": by_campaign,
            },
            ensure_ascii=False,
            default=_json_default,
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
