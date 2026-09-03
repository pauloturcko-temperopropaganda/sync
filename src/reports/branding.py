"""Assets de marca (Tempero Propaganda) embutidos como data-URI no
relatório, pra o PDF final ser um arquivo único e portável — sem
depender de um caminho de arquivo local pro Playwright carregar.

Os arquivos processados (logo branca, fontes) ficam em branding/,
copiados de brand/tempero-brand/ (fonte original enviada pelo
Paulo). Ver brand/ vs branding/ em sync_roadmap_ideas.md.

Cabeçalho decidido com o Paulo: preto + logo branca/laranja — é a
única variante usada nos relatórios reais (a versão clara, com logo
preta, foi descartada).
"""

from __future__ import annotations

import base64
from pathlib import Path

BRANDING_DIR = Path(__file__).resolve().parents[2] / "branding"


def _b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def logo_data_uri() -> str:
    return f"data:image/png;base64,{_b64(BRANDING_DIR / 'tempero-logo-white.png')}"


def font_data_uri(filename: str) -> str:
    return f"data:font/ttf;base64,{_b64(BRANDING_DIR / 'fonts' / filename)}"


def sync_logo_data_uri() -> str:
    return f"data:image/png;base64,{_b64(BRANDING_DIR / 'sync-logo-black.png')}"
