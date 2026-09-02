"""Ferramenta autorizada: consulta informações básicas de um cliente.

Uso:
    python -m src.ai_tools.get_client_info --client seed-cliente-teste

A ferramenta aceita somente o slug exato do cliente.
Não existe parâmetro para SQL arbitrário.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from decimal import Decimal

from .db import get_connection, fetch_one


def _json_default(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    raise TypeError(f"Tipo não serializável: {type(value).__name__}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Consulta informações básicas de um cliente do Sync."
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
                {"ok": False, "error": "O slug do cliente não pode ser vazio."},
                ensure_ascii=False,
            )
        )
        return 2

    # Consulta fixa e parametrizada.
    # Não aceitar SQL vindo da linha de comando é uma decisão de segurança.
    query = """
        SELECT
            clients.id,
            clients.name,
            clients.slug,
            clients.industry,
            clients.status,
            clients.created_at,
            clients.updated_at,

            organizations.id AS organization_id,
            organizations.slug AS organization_slug,
            organizations.name AS organization_name

        FROM clients

        INNER JOIN organizations
            ON organizations.id = clients.organization_id

        WHERE clients.slug = %s
        LIMIT 1
    """

    try:
        with get_connection() as connection:
            client = fetch_one(connection, query, (client_slug,))
    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "Falha ao consultar a ferramenta get_client_info.",
                    "details": str(exc),
                },
                ensure_ascii=False,
            )
        )
        return 1

    if client is None:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "Cliente não encontrado.",
                    "client_slug": client_slug,
                },
                ensure_ascii=False,
                default=_json_default,
            )
        )
        return 3

    print(
        json.dumps(
            {"ok": True, "client": client},
            ensure_ascii=False,
            default=_json_default,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
