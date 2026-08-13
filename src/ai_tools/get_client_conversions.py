"""Ferramenta autorizada: consulta conversões de um cliente.

Uso:

python -m src.ai_tools.get_client_conversions \
    --client seed-alpha-imoveis \
    --start 2026-07-01 \
    --end 2026-07-31

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
    """Converte tipos do MariaDB para JSON."""

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, Decimal):
        return float(value)

    raise TypeError(
        f"Tipo não serializável: {type(value).__name__}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Consulta conversões de um cliente do Sync."
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

    conversions_query = """
        SELECT
            conversions.id,
            conversions.type,
            conversions.value,
            conversions.conversion_date,

            conversions.lead_id,
            conversions.campaign_id,

            campaigns.name AS campaign_name

        FROM conversions

        LEFT JOIN campaigns
            ON campaigns.id = conversions.campaign_id

        INNER JOIN clients
            ON clients.id = conversions.client_id

        WHERE clients.slug = %s
          AND conversions.conversion_date BETWEEN %s AND %s

        ORDER BY conversions.conversion_date DESC,
                 conversions.id DESC
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

            conversions = fetch_all(
                connection,
                conversions_query,
                (
                    client_slug,
                    start_date,
                    end_date,
                ),
            )

    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "Falha ao consultar as conversões.",
                    "details": str(exc),
                },
                ensure_ascii=False,
            )
        )
        return 1

    total_conversions = len(conversions)

    total_value = sum(
        float(conversion["value"] or 0)
        for conversion in conversions
    )

    by_type: dict[str, int] = {}

    for conversion in conversions:
        conversion_type = conversion["type"]

        by_type[conversion_type] = (
            by_type.get(conversion_type, 0) + 1
        )

    print(
        json.dumps(
            {
                "ok": True,
                "client": client,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "summary": {
                    "total_conversions": total_conversions,
                    "total_value": round(total_value, 2),
                    "by_type": by_type,
                },
                "conversions": conversions,
            },
            ensure_ascii=False,
            default=_json_default,
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())