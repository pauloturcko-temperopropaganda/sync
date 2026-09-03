"""Geração dos gráficos de tendência diária do relatório, como PNG
em base64 (embutido direto no HTML, sem arquivo temporário separado
pro Playwright precisar carregar)."""

from __future__ import annotations

import base64
from io import BytesIO
from typing import Callable

import matplotlib

matplotlib.use("Agg")  # sem display — só gerar imagem
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

ACCENT_COLOR = "#111111"
GRID_COLOR = "#E5E7EB"
TEXT_COLOR = "#374151"


def _render_step_chart(
    daily_trend: list[dict],
    value_key: str,
    y_label: str,
    y_formatter: Callable[[float, float], str],
) -> str:
    """Retorna a string data-URI (data:image/png;base64,...) do
    gráfico. Estilo step (só ângulos de 90°) em todos os gráficos de
    tendência diária do relatório, por consistência visual entre eles
    — pedido explícito de estilo do relatório de investimento, mantido
    aqui pros novos."""

    dates = [row["metric_date"] for row in daily_trend]
    values = [float(row[value_key] or 0) for row in daily_trend]

    fig, ax = plt.subplots(figsize=(9, 3), dpi=150)

    if dates:
        ax.step(dates, values, where="mid", color=ACCENT_COLOR, linewidth=2)
        ax.fill_between(dates, values, step="mid", color=ACCENT_COLOR, alpha=0.08)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=10))
    else:
        ax.text(0.5, 0.5, "Sem dado no período", ha="center", va="center", color=TEXT_COLOR)

    ax.set_ylabel(y_label, color=TEXT_COLOR, fontsize=9)
    ax.yaxis.set_major_formatter(y_formatter)

    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(GRID_COLOR)

    ax.tick_params(colors=TEXT_COLOR, labelsize=8)
    ax.grid(axis="y", color=GRID_COLOR, linewidth=0.8)
    ax.set_axisbelow(True)

    fig.tight_layout()

    buffer = BytesIO()
    fig.savefig(buffer, format="png", transparent=True)
    plt.close(fig)

    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def render_daily_spend_chart(daily_trend: list[dict]) -> str:
    return _render_step_chart(
        daily_trend,
        "spend",
        "Investimento (R$)",
        lambda v, _: f"R$ {v:,.0f}".replace(",", "."),
    )


BRAND_ORANGE = "#E8A33D"
PIE_PALETTE = [ACCENT_COLOR, BRAND_ORANGE, "#9CA3AF", "#D1D5DB", "#4B5563"]


def _render_pie_chart(labels: list[str], values: list[float], colors: list[str]) -> str:
    fig, ax = plt.subplots(figsize=(6, 5), dpi=150)

    if sum(values) > 0:
        _, _, autotexts = ax.pie(
            values,
            labels=labels,
            autopct="%1.0f%%",
            startangle=90,
            colors=colors[: len(values)],
            wedgeprops={"edgecolor": "white", "linewidth": 1.5},
            textprops={"fontsize": 11, "color": TEXT_COLOR},
        )
        # autopct fica em cima da fatia (fundo escuro na maioria das
        # cores da paleta) — texto branco com contorno sutil pra não
        # sumir contra o preto/laranja, diferente dos rótulos de fora
        # (labels=), que ficam no fundo claro da página.
        for autotext in autotexts:
            autotext.set_color("white")
            autotext.set_fontweight("bold")
    else:
        ax.text(0.5, 0.5, "Sem dado no período", ha="center", va="center", color=TEXT_COLOR)

    ax.set_aspect("equal")
    fig.tight_layout()

    buffer = BytesIO()
    fig.savefig(buffer, format="png", transparent=True)
    plt.close(fig)

    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def render_platform_spend_chart(platform_breakdown: list[dict]) -> str:
    labels = [row["platform"].replace("_", " ").title() for row in platform_breakdown]
    values = [row["spend"] for row in platform_breakdown]
    return _render_pie_chart(labels, values, PIE_PALETTE)


def render_age_chart(by_age: list[dict]) -> str:
    """Barras agrupadas, cliques (eixo esquerdo) e leads (eixo
    direito) por faixa etária — dois eixos porque a ordem de grandeza
    entre as duas métricas costuma ser bem diferente (cliques na
    casa das centenas/milhares, leads na casa das dezenas)."""

    labels = [row["age_range"] for row in by_age]
    clicks = [row["clicks"] for row in by_age]
    leads = [row["leads"] for row in by_age]

    fig, ax_clicks = plt.subplots(figsize=(9, 3.2), dpi=150)
    ax_leads = ax_clicks.twinx()

    x = range(len(labels))
    width = 0.36
    ax_clicks.bar([i - width / 2 for i in x], clicks, width=width, color=ACCENT_COLOR, label="Cliques")
    ax_leads.bar([i + width / 2 for i in x], leads, width=width, color=BRAND_ORANGE, label="Leads")

    ax_clicks.set_xticks(list(x))
    ax_clicks.set_xticklabels(labels, fontsize=9, color=TEXT_COLOR)
    ax_clicks.set_ylabel("Cliques", color=TEXT_COLOR, fontsize=9)
    ax_leads.set_ylabel("Leads", color=TEXT_COLOR, fontsize=9)
    ax_clicks.yaxis.set_major_formatter(lambda v, _: f"{v:,.0f}".replace(",", "."))
    ax_leads.yaxis.set_major_formatter(lambda v, _: f"{v:,.0f}".replace(",", "."))

    for spine in ("top",):
        ax_clicks.spines[spine].set_visible(False)
        ax_leads.spines[spine].set_visible(False)
    ax_clicks.spines["left"].set_color(GRID_COLOR)
    ax_clicks.spines["bottom"].set_color(GRID_COLOR)
    ax_leads.spines["right"].set_color(GRID_COLOR)

    ax_clicks.tick_params(colors=TEXT_COLOR, labelsize=8)
    ax_leads.tick_params(colors=TEXT_COLOR, labelsize=8)
    ax_clicks.grid(axis="y", color=GRID_COLOR, linewidth=0.8)
    ax_clicks.set_axisbelow(True)

    handles = [
        plt.Rectangle((0, 0), 1, 1, color=ACCENT_COLOR),
        plt.Rectangle((0, 0), 1, 1, color=BRAND_ORANGE),
    ]
    ax_clicks.legend(handles, ["Cliques", "Leads"], loc="upper right", fontsize=8, frameon=False)

    fig.tight_layout()

    buffer = BytesIO()
    fig.savefig(buffer, format="png", transparent=True)
    plt.close(fig)

    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


GENDER_LABELS = {"female": "Mulher", "male": "Homem", "unknown": "Desconhecido"}


def render_gender_pie_chart(by_gender: list[dict]) -> str:
    labels = [GENDER_LABELS.get(row["gender"], row["gender"]) for row in by_gender]
    values = [row["leads"] for row in by_gender]
    return _render_pie_chart(labels, values, PIE_PALETTE)
