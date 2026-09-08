"""Vocabulário de seções extras do relatório — dados transversais ao
cliente inteiro (não amarrados a um objetivo de campanha específico,
diferente dos blocos em blocks.py). Cada seção pode ser incluída ou
não, independente de quais blocos foram escolhidos.

Faixa etária/gênero e região (Fase 2, 2026-09-08) usam os breakdowns
`age,gender` e `region` sincronizados por
src.integrations.meta_ads.sync — ver migration 0002. Diferente da
seção de plataforma (Fase 1), esses dois breakdowns vêm com `reach`
e `actions` utilizáveis, então dá pra mostrar leads por faixa etária/
gênero/região, não só métricas de mídia.
"""

from __future__ import annotations

PLATAFORMA = "plataforma"
CAMPANHAS = "campanhas"
DEMOGRAFIA = "demografia"
REGIAO = "regiao"
ANUNCIOS = "anuncios"

EXTRA_SECTIONS: dict[str, dict] = {
    PLATAFORMA: {"label": "Resultado por Plataforma"},
    CAMPANHAS: {"label": "Principais Campanhas"},
    DEMOGRAFIA: {"label": "Faixa Etária e Gênero"},
    REGIAO: {"label": "Regiões com Maior Alcance"},
    ANUNCIOS: {"label": "Principais Anúncios"},
}
