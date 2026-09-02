"""Dashboard de administração do Sync — status de sincronização e
botão pra forçar uma atualização manual.

Uso:
    python -m src.dashboard.app
    (abre em http://localhost:8050)

Leitura (cards de status) usa as credenciais somente-leitura
(sync_ai, via src.ai_tools.db) — igual ao gerador de relatório. Só o
botão de sincronizar usa as credenciais administrativas, e só depois
de validar a senha em DASHBOARD_ADMIN_PASSWORD (.env.admin).
"""

from __future__ import annotations

import os
import threading
from contextlib import redirect_stdout
from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from src.ai_tools.db import fetch_all, fetch_one, get_connection
from src.dashboard.state import sync_run_state
from src.integrations.meta_ads.sync import sync_all as run_meta_sync

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env.admin")

TEMPLATE_DIR = Path(__file__).parent / "templates"
BRANDING_DIR = PROJECT_ROOT / "branding"

app = FastAPI(title="Sync — Painel")
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))
app.mount("/branding", StaticFiles(directory=str(BRANDING_DIR)), name="branding")

DEFAULT_SYNC_DAYS = 7


def _admin_password() -> str:
    value = os.getenv("DASHBOARD_ADMIN_PASSWORD")
    if not value:
        raise RuntimeError("DASHBOARD_ADMIN_PASSWORD não configurado em .env.admin")
    return value


def _fetch_clients_status() -> list[dict]:
    with get_connection() as connection:
        return fetch_all(
            connection,
            """
            SELECT DISTINCT ON (ad_accounts.id)
                clients.name AS client_name,
                clients.slug AS client_slug,
                data_sync_runs.status,
                data_sync_runs.started_at,
                data_sync_runs.finished_at,
                data_sync_runs.records_processed,
                data_sync_runs.error_message
            FROM ad_accounts
            INNER JOIN clients ON clients.id = ad_accounts.client_id
            LEFT JOIN data_sync_runs ON data_sync_runs.ad_account_id = ad_accounts.id
            WHERE clients.slug NOT LIKE %s
            ORDER BY ad_accounts.id, data_sync_runs.started_at DESC NULLS LAST
            """,
            ("seed-%",),
        )


def _fetch_overview() -> dict:
    with get_connection() as connection:
        row = fetch_one(
            connection,
            """
            SELECT
                COUNT(DISTINCT clients.id) AS total_clients,
                COUNT(DISTINCT campaigns.id) AS total_campaigns,
                MIN(daily_metrics.metric_date) AS earliest_date,
                MAX(daily_metrics.metric_date) AS latest_date
            FROM clients
            LEFT JOIN ad_accounts ON ad_accounts.client_id = clients.id
            LEFT JOIN campaigns ON campaigns.ad_account_id = ad_accounts.id
            LEFT JOIN daily_metrics ON daily_metrics.campaign_id = campaigns.id
            WHERE clients.slug NOT LIKE %s
            """,
            ("seed-%",),
        )
        return row


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {})


@app.get("/api/status")
def api_status():
    return {
        "overview": _fetch_overview(),
        "clients": _fetch_clients_status(),
        "sync_run": sync_run_state.snapshot(),
    }


@app.get("/api/sync/log")
def api_sync_log():
    return sync_run_state.snapshot()


class SyncRequest(BaseModel):
    password: str


def _run_sync_in_background():
    stream = sync_run_state.start()
    ok = True
    try:
        with redirect_stdout(stream):
            until = date.today()
            since = until - timedelta(days=DEFAULT_SYNC_DAYS)
            results = run_meta_sync(since, until)
            ok = all(r["ok"] for r in results)
    except Exception as exc:
        print(f"ERRO INESPERADO: {type(exc).__name__}: {exc}")
        ok = False
    finally:
        sync_run_state.finish(ok)


@app.post("/api/sync")
def api_trigger_sync(payload: SyncRequest):
    if payload.password != _admin_password():
        raise HTTPException(status_code=403, detail="Senha incorreta.")

    if sync_run_state.running:
        raise HTTPException(status_code=409, detail="Já existe uma sincronização em andamento.")

    thread = threading.Thread(target=_run_sync_in_background, daemon=True)
    thread.start()
    return {"started": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.dashboard.app:app", host="127.0.0.1", port=8050, reload=False)
