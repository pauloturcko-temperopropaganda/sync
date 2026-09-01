"""Camada de acesso ao PostgreSQL para ferramentas da IA.

IMPORTANTE:

- Este módulo não aceita SQL arbitrário.
- As ferramentas devem fornecer consultas fixas e parametrizadas.
- A conta usada por estas ferramentas deve ter permissão somente de leitura.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row


# Carrega exclusivamente as credenciais destinadas à IA.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
AI_ENV_FILE = PROJECT_ROOT / ".env.agent"

load_dotenv(AI_ENV_FILE)


def _required_env(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise RuntimeError(
            f"Variável de ambiente obrigatória não configurada: {name}"
        )

    return value


@contextmanager
def get_connection() -> Generator[psycopg.Connection, None, None]:
    """Abre uma conexão somente para uso das ferramentas autorizadas."""

    connection = psycopg.connect(
        host=_required_env("SYNC_DB_HOST"),
        port=int(os.getenv("SYNC_DB_PORT", "5432")),
        user=_required_env("SYNC_DB_USER"),
        password=_required_env("SYNC_DB_PASSWORD"),
        dbname=os.getenv("SYNC_DB_NAME", "sync_db"),
        row_factory=dict_row,
        connect_timeout=5,
        autocommit=True,
        options="-c statement_timeout=10000",
    )

    try:
        yield connection
    finally:
        connection.close()


def fetch_one(
    connection: psycopg.Connection,
    query: str,
    params: tuple[Any, ...] = (),
) -> dict[str, Any] | None:
    """Executa uma consulta parametrizada que deve retornar no máximo uma linha."""

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        return cursor.fetchone()


def fetch_all(
    connection: psycopg.Connection,
    query: str,
    params: tuple[Any, ...] = (),
) -> list[dict[str, Any]]:
    """Executa uma consulta parametrizada e retorna todas as linhas."""

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        return list(cursor.fetchall())
