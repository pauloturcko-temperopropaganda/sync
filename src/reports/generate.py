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

from src.reports.branding import font_data_uri, logo_data_uri, sync_logo_data_uri
from src.reports.chart import (
    render_age_chart,
    render_daily_spend_chart,
    render_gender_pie_chart,
    render_platform_spend_chart,
)
from src.reports.data import load_report_data

TEMPLATE_DIR = Path(__file__).parent / "templates"


def render_html(data: dict) -> str:
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("client_report.html")

    return template.render(
        client=data["client"],
        period=data["period"],
        summary=data["summary"],
        daily_trend=data["daily_trend"],
        blocks=data["blocks"],
        show_platform=data["show_platform"],
        platform_breakdown=data["platform_breakdown"],
        show_campaigns=data["show_campaigns"],
        top_campaigns=data["top_campaigns"],
        show_demographics=data["show_demographics"],
        demographics=data["demographics"],
        show_region=data["show_region"],
        region_breakdown=data["region_breakdown"],
        show_ads=data["show_ads"],
        top_ads=data["top_ads"],
        chart_spend_uri=render_daily_spend_chart(data["daily_trend"]),
        chart_platform_uri=(
            render_platform_spend_chart(data["platform_breakdown"])
            if data["platform_breakdown"]
            else None
        ),
        chart_age_uri=(
            render_age_chart(data["demographics"]["by_age"])
            if data["demographics"] and data["demographics"]["by_age"]
            else None
        ),
        chart_gender_uri=(
            render_gender_pie_chart(data["demographics"]["by_gender"])
            if data["demographics"] and data["demographics"]["by_gender"]
            else None
        ),
        generated_at=datetime.now().strftime("%d/%m/%Y %H:%M"),
        logo_data_uri=logo_data_uri(),
        sync_logo_data_uri=sync_logo_data_uri(),
        font_extrabold_uri=font_data_uri("PublicSans-ExtraBold.ttf"),
        font_medium_uri=font_data_uri("PublicSans-Medium.ttf"),
    )


def html_to_pdf(html: str, out_path: Path) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html, wait_until="load")
        # Margem zero real no PDF (o Playwright não aplica a margem
        # do @page do CSS) — quem cria o espaçamento da página é o
        # próprio template, com <main> tendo padding e o cabeçalho
        # ocupando a borda física de verdade (pro fundo colorido
        # chegar até a beirada, sem sangria simulada via margem
        # negativa, que só funciona dentro de um contexto real de
        # página impressa).
        page.pdf(
            path=str(out_path),
            format="A4",
            print_background=True,
            margin={"top": "0mm", "right": "0mm", "bottom": "0mm", "left": "0mm"},
        )
        browser.close()


def generate_report(
    client_slug: str,
    start: date,
    end: date,
    out_path: Path,
    blocks: list[str] | None = None,
    extra: list[str] | None = None,
    drop_empty: bool = False,
) -> dict:
    """Retorna quais blocos/seções extras entraram no PDF
    (`included_blocks`/`included_extra`) e quais foram pedidos mas
    descartados por falta de dado no período (`excluded_blocks`/
    `excluded_extra`, só populado quando drop_empty=True — ver
    src.reports.data.load_report_data)."""

    data = load_report_data(client_slug, start, end, blocks=blocks, extra=extra, drop_empty=drop_empty)
    html = render_html(data)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    html_to_pdf(html, out_path)

    return {
        "included_blocks": [{"key": b["key"], "label": b["label"]} for b in data["blocks"]],
        "excluded_blocks": [{"key": b["key"], "label": b["label"]} for b in data["excluded_blocks"]],
        "included_extra": data["included_extra"],
        "excluded_extra": data["excluded_extra"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera relatório de performance em PDF.")
    parser.add_argument("--client", required=True, help="Slug do cliente.")
    parser.add_argument("--start", required=True, help="Data inicial YYYY-MM-DD.")
    parser.add_argument("--end", required=True, help="Data final YYYY-MM-DD.")
    parser.add_argument("--out", default=None, help="Caminho do PDF de saída.")
    parser.add_argument(
        "--blocks",
        default=None,
        help=(
            "Blocos de resultado a incluir, separados por vírgula "
            "(lead,whatsapp,trafego,engajamento,video,vendas). "
            "Se omitido, detecta automaticamente com base nas campanhas com investimento no período."
        ),
    )
    parser.add_argument(
        "--extra",
        default=None,
        help=(
            "Seções extras a incluir, separadas por vírgula (plataforma,campanhas). "
            "Se omitido, detecta automaticamente com base no dado disponível no período."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end)
    out_path = Path(args.out) if args.out else Path(f"reports_output/{args.client}_{start}_{end}.pdf")
    blocks = [b.strip() for b in args.blocks.split(",")] if args.blocks else None
    extra = [e.strip() for e in args.extra.split(",")] if args.extra else None

    try:
        generate_report(args.client, start, end, out_path, blocks=blocks, extra=extra)
    except ValueError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    print(f"Relatório gerado em: {out_path.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
