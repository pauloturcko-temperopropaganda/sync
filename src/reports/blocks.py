"""Vocabulário fixo de blocos de resultado que um relatório pode
incluir, além do bloco fixo de mídia paga que toda campanha tem.

Cada bloco representa um objetivo de campanha (Lead, WhatsApp,
Tráfego, Engajamento, Vídeo/Reconhecimento, Vendas) e mapeia pra um
action_type específico em daily_actions — não pra business_category
de action_type_catalog, porque a categoria canônica de "engagement"
é link_click (métrica do bloco fixo), enquanto o bloco de Engajamento
aqui precisa de post_engagement (engajamento total do post).

As campanhas de cada bloco são selecionadas pelo `objective`. Contas
reais têm campanhas com o vocabulário novo da Meta (OUTCOME_*) e
campanhas mais antigas, nunca recriadas, com o vocabulário legado
(LINK_CLICKS, REACH, etc) — por isso o mapa cobre os dois.
"""

from __future__ import annotations

LEAD = "lead"
WHATSAPP = "whatsapp"
TRAFEGO = "trafego"
ENGAJAMENTO = "engajamento"
VIDEO = "video"
VENDAS = "vendas"

OBJECTIVE_TO_BLOCK: dict[str, str] = {
    "OUTCOME_LEADS": LEAD,
    "LEAD_GENERATION": LEAD,
    "OUTCOME_TRAFFIC": TRAFEGO,
    "LINK_CLICKS": TRAFEGO,
    "OUTCOME_ENGAGEMENT": ENGAJAMENTO,
    "POST_ENGAGEMENT": ENGAJAMENTO,
    "PAGE_LIKES": ENGAJAMENTO,
    "EVENT_RESPONSES": ENGAJAMENTO,
    "OUTCOME_AWARENESS": VIDEO,
    "REACH": VIDEO,
    "BRAND_AWARENESS": VIDEO,
    "VIDEO_VIEWS": VIDEO,
    "MESSAGES": WHATSAPP,
    "OUTCOME_SALES": VENDAS,
    "CONVERSIONS": VENDAS,
    "PRODUCT_CATALOG_SALES": VENDAS,
}

BLOCKS: dict[str, dict] = {
    LEAD: {
        "label": "Leads",
        "action_types": ["lead"],
        "count_label": "Leads",
        "cost_label": "Custo por lead",
        # Detalhamento por origem: conferido contra payloads reais
        # (docs/meta-ads-api-exploracao/payloads/*_07_*.json) que
        # onsite_conversion.lead_grouped + offsite_conversion.fb_pixel_lead
        # bate exatamente com o total canônico 'lead' — não é garantido
        # pela documentação da Meta, só confirmado empiricamente nas
        # contas reais que já sincronizamos.
        "sub_metrics": [
            {
                "key": "lead_ads",
                "label": "Lead Ads (nativo)",
                "action_types": ["onsite_conversion.lead_grouped"],
            },
            {
                "key": "site",
                "label": "Leads no site",
                "action_types": ["offsite_conversion.fb_pixel_lead"],
            },
        ],
    },
    WHATSAPP: {
        "label": "WhatsApp",
        "action_types": ["onsite_conversion.messaging_conversation_started_7d"],
        "count_label": "Conversas iniciadas",
        "cost_label": "Custo por conversa",
    },
    TRAFEGO: {
        "label": "Tráfego",
        "action_types": ["landing_page_view"],
        "count_label": "Visualizações da página de destino",
        "cost_label": "Custo por visualização",
    },
    ENGAJAMENTO: {
        "label": "Engajamento",
        "action_types": ["post_engagement"],
        "count_label": "Engajamentos",
        "cost_label": "Custo por engajamento",
    },
    VIDEO: {
        "label": "Vídeo / Reconhecimento",
        "action_types": ["video_view"],
        "count_label": "Visualizações de vídeo",
        "cost_label": "Custo por resultado",
        "show_reach_frequency": True,
    },
    VENDAS: {
        "label": "Vendas",
        "action_types": ["purchase"],
        "count_label": "Compras",
        "cost_label": "Custo por compra",
        "show_value_and_roas": True,
    },
}


def objectives_for_block(block_key: str) -> list[str]:
    return [obj for obj, blk in OBJECTIVE_TO_BLOCK.items() if blk == block_key]
