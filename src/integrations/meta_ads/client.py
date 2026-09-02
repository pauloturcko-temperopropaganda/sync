"""Cliente HTTP fino para a Meta Marketing API (Graph API).

Usa o token do System User (.env.admin, escopo `ads_read`). Não é a
ferramenta de leitura da IA — isso aqui é camada administrativa,
usada só pelos scripts de sincronização em `sync.py`.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Iterator

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ADMIN_ENV_FILE = PROJECT_ROOT / ".env.admin"

load_dotenv(ADMIN_ENV_FILE)

GRAPH_VERSION = "v23.0"
BASE_URL = f"https://graph.facebook.com/{GRAPH_VERSION}"
REQUEST_TIMEOUT = 120

# Códigos de erro da Graph API conhecidos por serem transitórios
# (instabilidade momentânea do lado da Meta, rate limit) — vale
# tentar de novo. Qualquer outro código (parâmetro inválido,
# permissão negada etc.) falha na hora, sem retry: tentar de novo
# não vai corrigir um erro de configuração.
TRANSIENT_ERROR_CODES = {1, 2, 4, 17, 32, 613}
RETRY_DELAYS_SECONDS = [2, 5, 15]  # 3 retries = 4 tentativas no total


class MetaAdsAPIError(Exception):
    """Erro retornado pela Graph API (payload com chave "error")."""

    def __init__(self, message: str, payload: dict[str, Any]):
        super().__init__(message)
        self.payload = payload


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Variável de ambiente obrigatória não configurada: {name}")
    return value


def get_access_token() -> str:
    return _required_env("META_SYSTEM_USER_TOKEN")


def normalize_account_id(raw: str) -> str:
    raw = raw.strip()
    return raw if raw.startswith("act_") else f"act_{raw}"


def _is_transient(status_code: int, data: Any) -> bool:
    if status_code >= 500:
        return True
    if isinstance(data, dict):
        error_code = data.get("error", {}).get("code")
        if error_code in TRANSIENT_ERROR_CODES:
            return True
    return False


def _request_json(url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """GET com retry/backoff. Cobre três tipos de falha real que já
    aconteceram num backfill grande: erro de rede, resposta que não é
    JSON válido, e erros da Graph API marcados como transitórios."""

    last_error: Exception | None = None

    for attempt in range(len(RETRY_DELAYS_SECONDS) + 1):
        try:
            response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        except requests.exceptions.RequestException as exc:
            last_error = exc
        else:
            try:
                data = response.json()
            except ValueError as exc:
                last_error = exc
            else:
                if response.status_code >= 400 or "error" in data:
                    if not _is_transient(response.status_code, data):
                        error = data.get("error", {})
                        raise MetaAdsAPIError(
                            f"Graph API error: {error.get('message', 'erro desconhecido')}", data
                        )
                    last_error = MetaAdsAPIError(
                        f"Erro transitório da Graph API: {data.get('error', {}).get('message')}", data
                    )
                else:
                    return data

        if attempt < len(RETRY_DELAYS_SECONDS):
            delay = RETRY_DELAYS_SECONDS[attempt]
            print(f"  (falha transitória, tentativa {attempt + 1}: {last_error} — retry em {delay}s)")
            time.sleep(delay)

    raise MetaAdsAPIError(
        f"Falhou após {len(RETRY_DELAYS_SECONDS) + 1} tentativas: {last_error}", {}
    )


def get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Chamada GET simples (sem paginação) contra a Graph API."""

    params = dict(params or {})
    params["access_token"] = get_access_token()
    return _request_json(f"{BASE_URL}/{path}", params)


def get_all_pages(path: str, params: dict[str, Any] | None = None, max_pages: int = 50) -> Iterator[dict[str, Any]]:
    """Segue a paginação `paging.next` da Graph API, produzindo cada
    registro individualmente (generator, não carrega tudo na memória
    de uma vez para respostas grandes)."""

    page = get(path, params)
    pages_seen = 0

    while True:
        for item in page.get("data", []):
            yield item

        pages_seen += 1
        next_url = page.get("paging", {}).get("next")

        if not next_url or pages_seen >= max_pages:
            break

        page = _request_json(next_url)
