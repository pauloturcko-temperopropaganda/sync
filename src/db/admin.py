"""Camada de acesso administrativo ao PostgreSQL.

Este módulo é destinado exclusivamente a operações administrativas
executadas pelo desenvolvedor/administrador do sistema.

As credenciais administrativas nunca devem ser expostas às ferramentas
da IA.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ADMIN_ENV_FILE = PROJECT_ROOT / ".env.admin"

load_dotenv(ADMIN_ENV_FILE)


def _required_env(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise RuntimeError(
            f"Variável de ambiente obrigatória não configurada: {name}"
        )

    return value


@contextmanager
def get_connection() -> Generator[psycopg.Connection, None, None]:
    """Abre uma conexão administrativa com o banco."""

    connection = psycopg.connect(
        host=_required_env("DB_HOST"),
        port=int(os.getenv("DB_PORT", "5432")),
        user=_required_env("DB_USER"),
        password=_required_env("DB_PASSWORD"),
        dbname=os.getenv("DB_NAME", "sync_db"),
        row_factory=dict_row,
        connect_timeout=5,
        autocommit=False,
        options="-c statement_timeout=30000",
    )

    try:
        yield connection
    finally:
        connection.close()


def execute(
    connection: psycopg.Connection,
    query: str,
    params: tuple[Any, ...] = (),
) -> int:
    """Executa uma operação administrativa parametrizada."""

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        return cursor.rowcount
