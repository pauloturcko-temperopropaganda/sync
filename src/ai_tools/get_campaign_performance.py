"""Ferramenta autorizada: consulta desempenho de uma campanha.

Uso:

python -m src.ai_tools.get_campaign_performance --client seed-alpha-imoveis --campaign 1001 --start 2026-07-01 --end 2026-07-31

A ferramenta aceita parâmetros de negócio.
Não existe parâmetro para SQL arbitrário.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from src.ai_tools.db import fetch_one, get_connection


def _json_default(value: Any) -> Any:
    """Converte tipos do MariaDB para JSON."""
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
        help="ID da campanha.",
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

    query = """
        SELECT
            campaigns.id,
            campaigns.name,
            campaigns.status,

            clients.id AS client_id,
            clients.name AS client_name,
            clients.slug AS client_slug,

            COALESCE(SUM(daily_metrics.impressions), 0) AS impressions,
            COALESCE(SUM(daily_metrics.clicks), 0) AS clicks,
            COALESCE(SUM(daily_metrics.spend), 0) AS spend,
            COALESCE(SUM(daily_metrics.reach), 0) AS reach,
            COALESCE(SUM(daily_metrics.video_views), 0) AS video_views,
            COALESCE(
                SUM(daily_metrics.platform_conversions),
                0
            ) AS platform_conversions

        FROM campaigns

        INNER JOIN ad_accounts
            ON ad_accounts.id = campaigns.ad_account_id

        INNER JOIN clients
            ON clients.id = ad_accounts.client_id

        INNER JOIN ad_groups
            ON ad_groups.campaign_id = campaigns.id

        INNER JOIN ads
            ON ads.ad_group_id = ad_groups.id

        INNER JOIN daily_metrics
            ON daily_metrics.ad_id = ads.id
            AND daily_metrics.metric_date BETWEEN %s AND %s

        WHERE clients.slug = %s
          AND campaigns.id = %s

        GROUP BY
            campaigns.id,
            campaigns.name,
            campaigns.status,
            clients.id,
            clients.name,
            clients.slug

        LIMIT 1
    """

    try:
        with get_connection() as connection:
            result = fetch_one(
                connection,
                query,
                (
                    start_date,
                    end_date,
                    client_slug,
                    args.campaign,
                ),
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

    if result is None:
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

    impressions = int(result["impressions"] or 0)
    clicks = int(result["clicks"] or 0)
    spend = float(result["spend"] or 0)

    ctr = (clicks / impressions * 100) if impressions else 0
    cpc = (spend / clicks) if clicks else 0
    cpm = (spend / impressions * 1000) if impressions else 0

    metrics = {
        "impressions": impressions,
        "clicks": clicks,
        "spend": round(spend, 2),
        "reach": int(result["reach"] or 0),
        "video_views": int(result["video_views"] or 0),
        "platform_conversions": int(
            result["platform_conversions"] or 0
        ),
        "ctr_percent": round(ctr, 2),
        "cpc": round(cpc, 2),
        "cpm": round(cpm, 2),
    }

    print(
        json.dumps(
            {
                "ok": True,
                "client": {
                    "id": result["client_id"],
                    "name": result["client_name"],
                    "slug": result["client_slug"],
                },
                "campaign": {
                    "id": result["id"],
                    "name": result["name"],
                    "status": result["status"],
                },
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "metrics": metrics,
            },
            ensure_ascii=False,
            default=_json_default,
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())