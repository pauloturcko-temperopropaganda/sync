"""Ferramenta autorizada: consulta desempenho de uma campanha.

Uso:

python -m src.ai_tools.get_campaign_performance --client seed-cliente-teste --campaign 1 --start 2026-08-01 --end 2026-08-31

A ferramenta aceita parâmetros de negócio.
Não existe parâmetro para SQL arbitrário.

Notas de modelagem (ver docs/meta-ads-api-exploracao.md):

- Métricas e ações são agregadas apenas no grão "campanha inteira"
  (ad_group_id, ad_id, device e publisher_platform nulos em
  daily_metrics/daily_actions). Se um dia existir dado mais granular
  (por device, por anúncio) para a mesma campanha/data, ele NÃO entra
  nesta soma — isso evita contar a mesma métrica duas vezes.
- `reach` é somado dia a dia porque é o que a tabela guarda, mas
  alcance não é uma métrica aditiva (o mesmo usuário pode ser
  alcançado em dias diferentes). O campo retornado deixa isso
  explícito para não ser lido como alcance único do período.
- Ações (`daily_actions`) só entram no resultado quando marcadas
  `is_canonical = true` no `action_type_catalog` — evita contar o
  mesmo evento várias vezes sob nomes diferentes (ex.: um lead que
  aparece como `lead`, `onsite_web_lead` e outras 7 variantes ao
  mesmo tempo na Meta).
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

    raise TypeError(f"Tipo não serializável: {type(value).__name__}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Consulta o desempenho de uma campanha."
    )

    parser.add_argument(
        "--client",
        required=True,
        help="Slug exato do cliente.",
    )

    parser.add_argument(
        "--campaign",
        required=True,
        type=int,
        help="ID interno da campanha (não é o external_campaign_id da plataforma).",
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

    campaign_query = """
        SELECT
            campaigns.id,
            campaigns.name,
            campaigns.status,
            campaigns.objective,

            clients.id AS client_id,
            clients.name AS client_name,
            clients.slug AS client_slug,

            platforms.slug AS platform_slug

        FROM campaigns

        INNER JOIN ad_accounts
            ON ad_accounts.id = campaigns.ad_account_id

        INNER JOIN clients
            ON clients.id = ad_accounts.client_id

        INNER JOIN platforms
            ON platforms.id = ad_accounts.platform_id

        WHERE clients.slug = %s
          AND campaigns.id = %s

        LIMIT 1
    """

    # LEFT JOIN (não INNER JOIN): uma campanha sem métrica no período
    # deve retornar zeros, não "não encontrada". O filtro de grão
    # (ad_group_id/ad_id/device/publisher_platform nulos) vai dentro
    # do ON, não do WHERE, para não descartar a linha da campanha
    # quando não há nenhuma métrica no grão certo.
    metrics_query = """
        SELECT
            COALESCE(SUM(daily_metrics.impressions), 0) AS impressions,
            COALESCE(SUM(daily_metrics.clicks), 0) AS clicks,
            COALESCE(SUM(daily_metrics.spend), 0) AS spend,
            COALESCE(SUM(daily_metrics.reach), 0) AS reach_daily_sum

        FROM campaigns

        LEFT JOIN daily_metrics
            ON daily_metrics.campaign_id = campaigns.id
            AND daily_metrics.metric_date BETWEEN %s AND %s
            AND daily_metrics.ad_group_id IS NULL
            AND daily_metrics.ad_id IS NULL
            AND daily_metrics.device IS NULL
            AND daily_metrics.publisher_platform IS NULL

        WHERE campaigns.id = %s
    """

    # LEFT JOIN a partir do catálogo (não de daily_actions): garante
    # que toda categoria canônica apareça no resultado, mesmo com
    # zero eventos no período, em vez de simplesmente sumir.
    actions_query = """
        SELECT
            action_type_catalog.business_category,
            COALESCE(SUM(daily_actions.count), 0) AS total_count,
            COALESCE(SUM(daily_actions.value), 0) AS total_value

        FROM action_type_catalog

        LEFT JOIN daily_actions
            ON daily_actions.action_type = action_type_catalog.action_type
            AND daily_actions.campaign_id = %s
            AND daily_actions.metric_date BETWEEN %s AND %s
            AND daily_actions.ad_group_id IS NULL
            AND daily_actions.ad_id IS NULL

        WHERE action_type_catalog.is_canonical = true

        GROUP BY action_type_catalog.business_category
        ORDER BY action_type_catalog.business_category
    """

    try:
        with get_connection() as connection:
            campaign = fetch_one(
                connection,
                campaign_query,
                (client_slug, args.campaign),
            )

            if campaign is None:
                print(
                    json.dumps(
                        {
                            "ok": False,
                            "error": "Campanha não encontrada para este cliente.",
                            "client_slug": client_slug,
                            "campaign_id": args.campaign,
                        },
                        ensure_ascii=False,
                    )
                )
                return 3

            metrics_row = fetch_one(
                connection,
                metrics_query,
                (start_date, end_date, args.campaign),
            )

            actions_rows = fetch_all(
                connection,
                actions_query,
                (args.campaign, start_date, end_date),
            )

    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "Falha ao consultar o desempenho da campanha.",
                    "details": str(exc),
                },
                ensure_ascii=False,
            )
        )
        return 1

    impressions = int(metrics_row["impressions"] or 0)
    clicks = int(metrics_row["clicks"] or 0)
    spend = float(metrics_row["spend"] or 0)

    ctr = (clicks / impressions * 100) if impressions else 0
    cpc = (spend / clicks) if clicks else 0
    cpm = (spend / impressions * 1000) if impressions else 0

    metrics = {
        "impressions": impressions,
        "clicks": clicks,
        "spend": round(spend, 2),
        "reach_daily_sum": int(metrics_row["reach_daily_sum"] or 0),
        "reach_daily_sum_note": (
            "Soma do alcance diário, não é alcance único do período — "
            "o mesmo usuário pode ser contado em mais de um dia."
        ),
        "ctr_percent": round(ctr, 2),
        "cpc": round(cpc, 2),
        "cpm": round(cpm, 2),
    }

    actions = {
        row["business_category"]: {
            "count": float(row["total_count"] or 0),
            "value": float(row["total_value"] or 0),
        }
        for row in actions_rows
    }

    print(
        json.dumps(
            {
                "ok": True,
                "client": {
                    "id": campaign["client_id"],
                    "name": campaign["client_name"],
                    "slug": campaign["client_slug"],
                },
                "campaign": {
                    "id": campaign["id"],
                    "name": campaign["name"],
                    "status": campaign["status"],
                    "objective": campaign["objective"],
                    "platform": campaign["platform_slug"],
                },
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "metrics": metrics,
                "actions": actions,
            },
            ensure_ascii=False,
            default=_json_default,
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
