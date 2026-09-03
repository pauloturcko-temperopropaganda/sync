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
import tempfile
import threading
from contextlib import redirect_stdout
from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from src.ai_tools.db import fetch_all, fetch_one, get_connection
from src.dashboard.state import sync_run_state
from src.integrations.meta_ads.accounts import ACCOUNTS
from src.integrations.meta_ads.sync import sync_all as run_meta_sync
from src.reports.blocks import BLOCKS
from src.reports.data import detect_available_blocks, detect_available_extra_sections, load_report_data
from src.reports.generate import generate_report, render_html
from src.reports.sections import EXTRA_SECTIONS

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
                MAX(daily_metrics.metric_date) AS latest_date,
                MAX(data_sync_runs.started_at) AS last_sync_at
            FROM clients
            LEFT JOIN ad_accounts ON ad_accounts.client_id = clients.id
            LEFT JOIN campaigns ON campaigns.ad_account_id = ad_accounts.id
            LEFT JOIN daily_metrics ON daily_metrics.campaign_id = campaigns.id
            LEFT JOIN data_sync_runs ON data_sync_runs.ad_account_id = ad_accounts.id
            WHERE clients.slug NOT LIKE %s
            """,
            ("seed-%",),
        )
        return row


def _parse_date(value: str, field: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Data inválida em '{field}': {value}")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {})


@app.get("/relatorios", response_class=HTMLResponse)
def relatorios_page(request: Request):
    return templates.TemplateResponse(request, "relatorios.html", {})


@app.get("/api/clients")
def api_clients():
    with get_connection() as connection:
        return fetch_all(
            connection,
            "SELECT slug, name FROM clients WHERE slug NOT LIKE %s ORDER BY name",
            ("seed-%",),
        )


@app.get("/api/report/blocks")
def api_report_blocks(client: str, start: str, end: str):
    start_d = _parse_date(start, "start")
    end_d = _parse_date(end, "end")
    with get_connection() as connection:
        available = set(detect_available_blocks(connection, client, start_d, end_d))
    return {
        "blocks": [
            {"key": key, "label": block["label"], "has_data": key in available}
            for key, block in BLOCKS.items()
        ]
    }


@app.get("/api/report/extra-sections")
def api_report_extra_sections(client: str, start: str, end: str):
    start_d = _parse_date(start, "start")
    end_d = _parse_date(end, "end")
    with get_connection() as connection:
        available = set(detect_available_extra_sections(connection, client, start_d, end_d))
    return {
        "sections": [
            {"key": key, "label": section["label"], "has_data": key in available}
            for key, section in EXTRA_SECTIONS.items()
        ]
    }


@app.get("/api/report/preview", response_class=HTMLResponse)
def api_report_preview(client: str, start: str, end: str, blocks: str = "", extra: str = ""):
    start_d = _parse_date(start, "start")
    end_d = _parse_date(end, "end")
    block_list = [b for b in blocks.split(",") if b] or None
    extra_list = [e for e in extra.split(",") if e] or None
    try:
        data = load_report_data(client, start_d, end_d, blocks=block_list, extra=extra_list)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return HTMLResponse(render_html(data))


@app.get("/api/report/pdf")
def api_report_pdf(client: str, start: str, end: str, blocks: str = "", extra: str = ""):
    start_d = _parse_date(start, "start")
    end_d = _parse_date(end, "end")
    block_list = [b for b in blocks.split(",") if b] or None
    extra_list = [e for e in extra.split(",") if e] or None

    with tempfile.TemporaryDirectory() as tmp_dir:
        out_path = Path(tmp_dir) / "relatorio.pdf"
        try:
            generate_report(client, start_d, end_d, out_path, blocks=block_list, extra=extra_list)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        pdf_bytes = out_path.read_bytes()

    filename = f"relatorio_{client}_{start_d}_{end_d}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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
    client_slug: str | None = None
    start: str | None = None
    end: str | None = None


def _run_sync_in_background(client_slug: str | None, since: date, until: date):
    stream = sync_run_state.start()
    ok = True
    try:
        with redirect_stdout(stream):
            results = run_meta_sync(since, until, only=client_slug)
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

    until = _parse_date(payload.end, "end") if payload.end else date.today()
    since = _parse_date(payload.start, "start") if payload.start else until - timedelta(days=DEFAULT_SYNC_DAYS)

    if since > until:
        raise HTTPException(status_code=400, detail="A data inicial não pode ser maior que a data final.")

    client_slug = payload.client_slug or None
    if client_slug is not None and client_slug not in {a.client_slug for a in ACCOUNTS}:
        raise HTTPException(status_code=404, detail=f"Cliente não configurado: {client_slug}")

    thread = threading.Thread(
        target=_run_sync_in_background, args=(client_slug, since, until), daemon=True
    )
    thread.start()
    return {"started": True}


if __name__ == "__main__":
    import uvicorn

    # 0.0.0.0 em vez de 127.0.0.1: escuta em todas as interfaces de
    # rede da máquina, não só localhost — é isso que permite outros
    # PCs na mesma rede local acessarem via http://<ip-desta-máquina>:8050,
    # em vez de só quem está sentado neste computador. Ainda exige
    # liberar a porta no firewall do Windows (não dá pra fazer isso
    # por aqui, precisa de admin) e o Postgres continua só local —
    # só o dashboard fica exposto na rede, o banco nunca sai desta
    # máquina.
    uvicorn.run("src.dashboard.app:app", host="0.0.0.0", port=8050, reload=False)
