"""Camada de acesso administrativo ao MariaDB.

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

import pymysql
from dotenv import load_dotenv
from pymysql.cursors import DictCursor


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
def get_connection() -> Generator[pymysql.connections.Connection, None, None]:
    """Abre uma conexão administrativa com o banco."""

    connection = pymysql.connect(
        host=_required_env("DB_HOST"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=_required_env("DB_USER"),
        password=_required_env("DB_PASSWORD"),
        database=os.getenv("DB_NAME", "sync_db"),
        cursorclass=DictCursor,
        connect_timeout=5,
        read_timeout=30,
        write_timeout=30,
        autocommit=False,
        charset="utf8mb4",
    )

    try:
        yield connection
    finally:
        connection.close()


def execute(
    connection: pymysql.connections.Connection,
    query: str,
    params: tuple[Any, ...] = (),
) -> int:
    """Executa uma operação administrativa parametrizada."""

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        return cursor.rowcount
