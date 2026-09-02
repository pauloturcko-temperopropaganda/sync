"""Gera o relatório de performance de um cliente em PDF.

Uso:

python -m src.reports.generate --client hospital-de-olhos-videira --start 2026-06-03 --end 2026-09-01 --out relatorio.pdf

Camada somente leitura (usa src.reports.data, que por sua vez usa as
credenciais restritas sync_ai) — geração de relatório nunca escreve
no banco.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright

from src.reports.chart import render_daily_spend_chart
from src.reports.data import load_report_data

TEMPLATE_DIR = Path(__file__).parent / "templates"

BUSINESS_CATEGORY_LABELS = {
    "lead": "Leads",
    "purchase": "Compras",
    "message": "Mensagens",
    "checkout": "Início de compra",
    "pageview": "Visualizações de página",
    "video": "Visualizações de vídeo",
    "engagement": "Engajamento",
    "other": "Outras ações",
}


def render_html(data: dict) -> str:
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("client_report.html")

    actions = [
        {
            "label": BUSINESS_CATEGORY_LABELS.get(row["business_category"], row["business_category"]),
            "total_count": float(row["total_count"] or 0),
        }
        for row in data["actions"]
    ]

    return template.render(
        client=data["client"],
        period=data["period"],
        summary=data["summary"],
        daily_trend=data["daily_trend"],
        actions=actions,
        top_campaigns=data["top_campaigns"],
        chart_data_uri=render_daily_spend_chart(data["daily_trend"]),
        generated_at=datetime.now().strftime("%d/%m/%Y %H:%M"),
    )


def html_to_pdf(html: str, out_path: Path) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html, wait_until="load")
        page.pdf(path=str(out_path), format="A4", print_background=True)
        browser.close()


def generate_report(client_slug: str, start: date, end: date, out_path: Path) -> None:
    data = load_report_data(client_slug, start, end)
    html = render_html(data)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    html_to_pdf(html, out_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera relatório de performance em PDF.")
    parser.add_argument("--client", required=True, help="Slug do cliente.")
    parser.add_argument("--start", required=True, help="Data inicial YYYY-MM-DD.")
    parser.add_argument("--end", required=True, help="Data final YYYY-MM-DD.")
    parser.add_argument("--out", default=None, help="Caminho do PDF de saída.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end)
    out_path = Path(args.out) if args.out else Path(f"reports_output/{args.client}_{start}_{end}.pdf")

    try:
        generate_report(args.client, start, end, out_path)
    except ValueError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    print(f"Relatório gerado em: {out_path.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
