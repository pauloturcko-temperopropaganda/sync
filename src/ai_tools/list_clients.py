"""Ferramenta autorizada: lista todos os clientes reais cadastrados
no Sync (slug, nome, indústria).

Existe pra resolver um problema concreto: todas as outras ferramentas
do catálogo exigem o slug exato do cliente (ex.: "hospital-de-olhos-
videira"), mas quem pede algo em linguagem natural normalmente só
sabe o nome comercial (ex.: "Hospital de Olhos"). Esta ferramenta
deixa o agente resolver nome -> slug sozinho, sem precisar adivinhar
nem olhar `src/integrations/meta_ads/accounts.py` diretamente (esse
arquivo é de configuração administrativa, fora do catálogo de
ferramentas autorizadas para o agente).

Uso:

    python -m src.ai_tools.list_clients
"""

from __future__ import annotations

import json
import sys

from src.ai_tools.db import fetch_all, get_connection


def main() -> int:
    query = """
        SELECT clients.slug, clients.name, clients.industry
        FROM clients
        WHERE clients.slug NOT LIKE %s
        ORDER BY clients.name
    """

    try:
        with get_connection() as connection:
            clients = fetch_all(connection, query, ("seed-%",))
    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "Falha ao listar clientes.",
                    "details": str(exc),
                },
                ensure_ascii=False,
            )
        )
        return 1

    print(json.dumps({"ok": True, "clients": clients}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
