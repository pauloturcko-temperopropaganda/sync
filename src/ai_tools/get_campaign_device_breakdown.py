"""Ferramenta autorizada: consulta o desempenho de uma campanha
quebrado por device e plataforma de publicação (device, publisher_
platform), no grão em que a Meta normalmente entrega essa segmentação.

Uso:

python -m src.ai_tools.get_campaign_device_breakdown --client seed-cliente-teste --campaign 2 --start 2026-08-01 --end 2026-08-05

A ferramenta aceita parâmetros de negócio.
Não existe parâmetro para SQL arbitrário.

Complementa `get_campaign_performance`, que deliberadamente ignora
linhas segmentadas por device/publisher_platform no seu agregado
(para não contar a mesma métrica duas vezes). Esta ferramenta é o
lugar certo para consultar exatamente essas linhas.

`publisher_platform` é conceito específico do Meta (facebook,
instagram, audience_network, threads) — fica nulo para campanhas de
outras plataformas, então uma linha pode aparecer só com `device`
preenchido, dependendo de como os dados foram sincronizados.
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
        description="Consulta o desempenho de uma campanha quebrado por device/plataforma."
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
        help="ID interno da campanha (o campo 'id' retornado por get_client_campaigns).",
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

    campaign_query = """
        SELECT
            campaigns.id,
            campaigns.name,
            campaigns.status,

            clients.id AS client_id,
            clients.name AS client_name,
            clients.slug AS client_slug

        FROM campaigns

        INNER JOIN ad_accounts
            ON ad_accounts.id = campaigns.ad_account_id

        INNER JOIN clients
            ON clients.id = ad_accounts.client_id

        WHERE clients.slug = %s
          AND campaigns.id = %s

        LIMIT 1
    """

    # Só linhas com pelo menos device ou publisher_platform
    # preenchido, e só no grão campanha (ad_group_id/ad_id nulos) —
    # não mistura com um possível detalhamento futuro por anúncio.
    breakdown_query = """
        SELECT
            daily_metrics.device,
            daily_metrics.publisher_platform,
            SUM(daily_metrics.impressions) AS impressions,
            SUM(daily_metrics.clicks) AS clicks,
            SUM(daily_metrics.spend) AS spend

        FROM daily_metrics

        WHERE daily_metrics.campaign_id = %s
          AND daily_metrics.metric_date BETWEEN %s AND %s
          AND daily_metrics.ad_group_id IS NULL
          AND daily_metrics.ad_id IS NULL
          AND (daily_metrics.device IS NOT NULL OR daily_metrics.publisher_platform IS NOT NULL)

        GROUP BY daily_metrics.device, daily_metrics.publisher_platform
        ORDER BY spend DESC
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

            breakdown_rows = fetch_all(
                connection,
                breakdown_query,
                (args.campaign, start_date, end_date),
            )

    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "Falha ao consultar a quebra por device/plataforma.",
                    "details": str(exc),
                },
                ensure_ascii=False,
            )
        )
        return 1

    breakdown = [
        {
            "device": row["device"],
            "publisher_platform": row["publisher_platform"],
            "impressions": int(row["impressions"] or 0),
            "clicks": int(row["clicks"] or 0),
            "spend": round(float(row["spend"] or 0), 2),
        }
        for row in breakdown_rows
    ]

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
                },
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "breakdown": breakdown,
                "count": len(breakdown),
            },
            ensure_ascii=False,
            default=_json_default,
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
