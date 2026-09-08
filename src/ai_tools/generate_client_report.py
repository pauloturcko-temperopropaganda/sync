"""Ferramenta autorizada: gera o relatório de performance em PDF de
um cliente, incluindo só os blocos de resultado pedidos que
realmente tiverem dado no período.

Diferença importante em relação ao relatório gerado pelo dashboard
(que mostra checkboxes com o que tem dado ou não, antes de gerar):
aqui quem chama não tem como ver isso de antemão, então um bloco
pedido sem dado no período é DESCARTADO em silêncio do PDF — não
aparece como seção "sem dado", que pareceria bug do Sync pra quem não
sabe que o cliente simplesmente não rodou aquele tipo de campanha.
O motivo do descarte volta em `excluded_blocks`; quem chamou esta
ferramenta deve contar isso pro usuário na resposta (ex.: "não
incluí Tráfego porque a Empresa X não teve investimento nesse
objetivo entre 01/08 e 31/08 — quer que eu inclua mesmo assim, vazio?"),
em vez de tratar a ausência como resultado normal e não comentar nada.

Uso:

python -m src.ai_tools.generate_client_report --client hospital-de-olhos-videira --start 2026-08-01 --end 2026-08-31 --blocks lead,whatsapp

Blocos válidos: lead, whatsapp, trafego, engajamento, video, vendas.
Seções extras válidas (--extra, mesma lógica de três formas de uso):
plataforma, campanhas, demografia, regiao, anuncios.

Três formas de usar --blocks, conforme o pedido do usuário:

- Omitido (parâmetro nem passado): detecta sozinho todos os blocos
  que têm dado real no período e inclui todos — é o fallback padrão
  quando o usuário pede "o relatório" sem especificar quais
  informações quer. Nunca aparece bloco vazio nesse modo (só entra o
  que existe de verdade).
- Lista explícita (ex.: "lead,whatsapp"): usuário pediu métricas
  específicas — inclui só essas, descartando (com aviso em
  `excluded_blocks`) as que não tiverem dado, a menos que --force
  seja passado.
- Vazio ("", string vazia mesmo): usuário pediu explicitamente só o
  resumo geral de mídia paga, sem nenhum bloco de resultado.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from src.reports.blocks import BLOCKS
from src.reports.generate import generate_report
from src.reports.sections import EXTRA_SECTIONS

REPORTS_OUTPUT_DIR = Path("reports_output")


def _json_default(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    raise TypeError(f"Tipo não serializável: {type(value).__name__}")


def _error(message: str, code: int, **extra: Any) -> int:
    print(json.dumps({"ok": False, "error": message, **extra}, ensure_ascii=False))
    return code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera o relatório de performance em PDF de um cliente do Sync."
    )
    parser.add_argument("--client", required=True, help="Slug exato do cliente.")
    parser.add_argument("--start", required=True, help="Data inicial no formato YYYY-MM-DD.")
    parser.add_argument("--end", required=True, help="Data final no formato YYYY-MM-DD.")
    parser.add_argument(
        "--blocks",
        default=None,
        help=(
            "Blocos de resultado pedidos, separados por vírgula. "
            f"Válidos: {', '.join(BLOCKS.keys())}. Omitido = detecta sozinho tudo que "
            "tiver dado real (fallback padrão). Vazio ('') = só o resumo fixo de mídia "
            "paga, sem bloco de resultado."
        ),
    )
    parser.add_argument(
        "--extra",
        default=None,
        help=(
            "Seções extras pedidas, separadas por vírgula. "
            f"Válidas: {', '.join(EXTRA_SECTIONS.keys())}. Omitido = detecta sozinho tudo que "
            "tiver dado real (fallback padrão). Vazio ('') = nenhuma seção extra, só os blocos."
        ),
    )
    parser.add_argument("--out", default=None, help="Caminho do PDF de saída (opcional).")
    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Inclui todos os blocos pedidos mesmo sem dado no período (aparecem como "
            "'sem dado' no PDF). Use só quando o usuário confirmar explicitamente que "
            "quer o bloco vazio mesmo assim, depois de avisado pelo 'excluded_blocks' "
            "de uma chamada anterior sem --force."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    client_slug = args.client.strip()
    if not client_slug:
        return _error("O slug do cliente não pode ser vazio.", 2)

    try:
        start_date = date.fromisoformat(args.start)
        end_date = date.fromisoformat(args.end)
    except ValueError:
        return _error("As datas devem estar no formato YYYY-MM-DD.", 2)

    if start_date > end_date:
        return _error("A data inicial não pode ser maior que a data final.", 2)

    if args.blocks is None:
        requested_blocks = None  # aciona a autodetecção (só o que tem dado real)
    else:
        requested_blocks = [b.strip() for b in args.blocks.split(",") if b.strip()]
        unknown = [b for b in requested_blocks if b not in BLOCKS]
        if unknown:
            return _error(
                f"Bloco(s) desconhecido(s): {', '.join(unknown)}.",
                2,
                valid_blocks=list(BLOCKS.keys()),
            )

    if args.extra is None:
        requested_extra = None  # aciona a autodetecção (só o que tem dado real)
    else:
        requested_extra = [e.strip() for e in args.extra.split(",") if e.strip()]
        unknown_extra = [e for e in requested_extra if e not in EXTRA_SECTIONS]
        if unknown_extra:
            return _error(
                f"Seção(ões) desconhecida(s): {', '.join(unknown_extra)}.",
                2,
                valid_extra=list(EXTRA_SECTIONS.keys()),
            )

    out_path = (
        Path(args.out)
        if args.out
        else REPORTS_OUTPUT_DIR / f"{client_slug}_{start_date}_{end_date}.pdf"
    )

    # Com --blocks/--extra omitidos, a autodetecção já só traz o que tem
    # dado real — drop_empty não tem o que descartar nesse caso.
    drop_empty = (requested_blocks is not None or requested_extra is not None) and not args.force

    try:
        result = generate_report(
            client_slug,
            start_date,
            end_date,
            out_path,
            blocks=requested_blocks,
            extra=requested_extra,
            drop_empty=drop_empty,
        )
    except ValueError as exc:
        return _error(str(exc), 3)
    except Exception as exc:
        return _error("Falha ao gerar o relatório.", 1, details=str(exc))

    print(
        json.dumps(
            {
                "ok": True,
                "client_slug": client_slug,
                "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
                "pdf_path": str(out_path.resolve()),
                "included_blocks": result["included_blocks"],
                "excluded_blocks": result["excluded_blocks"],
                "included_extra": result["included_extra"],
                "excluded_extra": result["excluded_extra"],
                "note": (
                    "Itens em 'excluded_blocks'/'excluded_extra' foram pedidos mas não "
                    "tinham dado real no período, por isso não entraram no PDF. Avise o "
                    "usuário do motivo em vez de tratar como resultado silencioso. Se ele "
                    "confirmar que quer o item mesmo vazio, chame de novo com --force."
                ),
            },
            ensure_ascii=False,
            default=_json_default,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
