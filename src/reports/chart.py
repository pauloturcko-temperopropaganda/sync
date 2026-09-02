"""Geração do gráfico de investimento diário do relatório, como PNG
em base64 (embutido direto no HTML, sem arquivo temporário separado
pro Playwright precisar carregar)."""

from __future__ import annotations

import base64
from io import BytesIO

import matplotlib

matplotlib.use("Agg")  # sem display — só gerar imagem
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

ACCENT_COLOR = "#111111"
GRID_COLOR = "#E5E7EB"
TEXT_COLOR = "#374151"


def render_daily_spend_chart(daily_trend: list[dict]) -> str:
    """Retorna a string data-URI (data:image/png;base64,...) do gráfico."""

    dates = [row["metric_date"] for row in daily_trend]
    spend = [float(row["spend"] or 0) for row in daily_trend]

    fig, ax = plt.subplots(figsize=(9, 3), dpi=150)

    if dates:
        ax.plot(dates, spend, color=ACCENT_COLOR, linewidth=2)
        ax.fill_between(dates, spend, color=ACCENT_COLOR, alpha=0.08)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=10))
    else:
        ax.text(0.5, 0.5, "Sem dado no período", ha="center", va="center", color=TEXT_COLOR)

    ax.set_ylabel("Investimento (R$)", color=TEXT_COLOR, fontsize=9)
    ax.yaxis.set_major_formatter(lambda v, _: f"R$ {v:,.0f}".replace(",", "."))

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
