"""Ferramenta autorizada: lista as campanhas de um cliente.

Uso:
python -m src.ai_tools.get_client_campaigns --client seed-cliente-teste

A ferramenta aceita somente o slug exato do cliente.
Não existe parâmetro para SQL arbitrário.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from src.ai_tools.db import fetch_all, get_connection


def _json_default(value: Any) -> Any:
    """Converte tipos do Postgres para JSON."""
    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, Decimal):
        return float(value)

    raise TypeError(f"Tipo não serializável: {type(value).__name__}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lista as campanhas de um cliente do Sync."
    )

    parser.add_argument(
        "--client",
        required=True,
        help="Slug exato do cliente. Ex.: seed-cliente-teste",
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

    # Consulta fixa para validar a existência do cliente.
    query = """
        SELECT
            clients.id,
            clients.name,
            clients.slug,
            clients.industry,
            clients.status
        FROM clients
        WHERE clients.slug = %s
        LIMIT 1
    """

    # Consulta fixa e parametrizada das campanhas.
    campaigns_query = """
        SELECT
            campaigns.id,
            campaigns.external_campaign_id,
            campaigns.name,
            campaigns.objective,
            campaigns.status,
            campaigns.start_date,
            campaigns.end_date,

            ad_accounts.id AS ad_account_id,
            ad_accounts.external_account_id,
            ad_accounts.name AS ad_account_name,
            ad_accounts.currency,
            ad_accounts.timezone,

            platforms.id AS platform_id,
            platforms.name AS platform_name,
            platforms.slug AS platform_slug

        FROM campaigns

        INNER JOIN ad_accounts
            ON ad_accounts.id = campaigns.ad_account_id

        INNER JOIN clients
            ON clients.id = ad_accounts.client_id

        INNER JOIN platforms
            ON platforms.id = ad_accounts.platform_id

        WHERE clients.slug = %s

        ORDER BY campaigns.id
    """

    try:
        with get_connection() as connection:
            client = fetch_all(
                connection,
                query,
                (client_slug,),
            )

            if not client:
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

            campaigns = fetch_all(
                connection,
                campaigns_query,
                (client_slug,),
            )

    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "Falha ao consultar as campanhas do cliente.",
                    "details": str(exc),
                },
                ensure_ascii=False,
            )
        )
        return 1

    print(
        json.dumps(
            {
                "ok": True,
                "client": client[0],
                "campaigns": campaigns,
                "count": len(campaigns),
            },
            ensure_ascii=False,
            default=_json_default,
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
