"""Consultas de dados para o gerador de relatório em PDF.

Camada somente leitura — usa as mesmas credenciais restritas
(sync_ai, via src.ai_tools.db) que as ferramentas de IA, não as
credenciais administrativas. Um relatório não deveria conseguir
escrever no banco.

As agregações seguem a mesma regra de grão já usada em
src/ai_tools/*.py: pra pegar só a linha "base" (uma por campanha/dia,
sem quebrar por nenhuma dimensão), TODAS as colunas de breakdown
precisam estar NULL — em daily_metrics: ad_group_id, ad_id, device,
publisher_platform, age_range, region; em daily_actions: ad_group_id,
ad_id, age_range, region, publisher_platform.

IMPORTANTE (bug real já cometido, 2026-09-08): faltar qualquer uma
dessas colunas no filtro NÃO dá erro nem linha faltando — dá
contagem A MAIS. Cada breakdown novo (Fase 2: idade/gênero, região;
Fase "cadastros por plataforma") grava uma segunda (ou terceira,
quarta...) linha pra cada campanha/dia, com o mesmo total repartido
por categoria — a soma de cada breakdown bate exatamente com a linha
base. Uma query que esqueça de excluir uma dessas dimensões soma a
base MAIS esse breakdown inteiro de novo, inflando o resultado (foi
assim que "leads" apareceu ~3x maior que o Meta Ads Manager mostrava
pro cliente). Toda vez que uma dimensão nova for adicionada a
daily_metrics/daily_actions, TODAS as queries de agregação "grão
base" desse arquivo e de src/ai_tools/*.py precisam ganhar mais um
`IS NULL` pra ela.
"""

from __future__ import annotations

from datetime import date

from src.ai_tools.db import fetch_all, fetch_one, get_connection
from src.reports.blocks import BLOCKS, OBJECTIVE_TO_BLOCK, objectives_for_block
from src.reports.sections import ANUNCIOS, CAMPANHAS, DEMOGRAFIA, EXTRA_SECTIONS, PLATAFORMA, REGIAO

AGE_RANGE_ORDER = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+", "unknown"]


def get_client(connection, client_slug: str) -> dict | None:
    return fetch_one(
        connection,
        "SELECT id, name, slug, industry FROM clients WHERE slug = %s LIMIT 1",
        (client_slug,),
    )


def get_summary(connection, client_slug: str, start: date, end: date) -> dict:
    """Cliques/CTR/CPC aqui são "de todos os cliques" (coluna `clicks`
    do insight, que inclui reação/compartilhar/etc, não só clique no
    link) — de propósito para bater com a métrica padrão "Cliques
    (todos)" que relatórios de mídia paga costumam usar como
    principal, em vez de só cliques no link (métrica mais estreita,
    que era o que este resumo usava antes)."""

    row = fetch_one(
        connection,
        """
        SELECT
            COALESCE(SUM(daily_metrics.impressions), 0) AS impressions,
            COALESCE(SUM(daily_metrics.spend), 0) AS spend,
            COALESCE(SUM(daily_metrics.reach), 0) AS reach,
            COALESCE(SUM(daily_metrics.clicks), 0) AS clicks
        FROM campaigns
        INNER JOIN ad_accounts ON ad_accounts.id = campaigns.ad_account_id
        INNER JOIN clients ON clients.id = ad_accounts.client_id
        LEFT JOIN daily_metrics
            ON daily_metrics.campaign_id = campaigns.id
            AND daily_metrics.metric_date BETWEEN %s AND %s
            AND daily_metrics.ad_group_id IS NULL
            AND daily_metrics.ad_id IS NULL
            AND daily_metrics.device IS NULL
            AND daily_metrics.publisher_platform IS NULL
            AND daily_metrics.age_range IS NULL
            AND daily_metrics.region IS NULL
        WHERE clients.slug = %s
        """,
        (start, end, client_slug),
    )

    impressions = int(row["impressions"] or 0)
    spend = float(row["spend"] or 0)
    reach = int(row["reach"] or 0)
    clicks = int(row["clicks"] or 0)

    return {
        "spend": spend,
        "impressions": impressions,
        "reach": reach,
        "frequency": (impressions / reach) if reach else 0,
        "cpm": (spend / impressions * 1000) if impressions else 0,
        "clicks": clicks,
        "ctr_percent": (clicks / impressions * 100) if impressions else 0,
        "cpc": (spend / clicks) if clicks else 0,
    }


def get_block_data(
    connection, client_slug: str, start: date, end: date, block_key: str
) -> dict:
    block = BLOCKS[block_key]
    objectives = objectives_for_block(block_key)

    campaign_row = fetch_one(
        connection,
        """
        SELECT
            COALESCE(SUM(daily_metrics.spend), 0) AS spend,
            COALESCE(SUM(daily_metrics.impressions), 0) AS impressions,
            COALESCE(SUM(daily_metrics.reach), 0) AS reach
        FROM campaigns
        INNER JOIN ad_accounts ON ad_accounts.id = campaigns.ad_account_id
        INNER JOIN clients ON clients.id = ad_accounts.client_id
        LEFT JOIN daily_metrics
            ON daily_metrics.campaign_id = campaigns.id
            AND daily_metrics.metric_date BETWEEN %s AND %s
            AND daily_metrics.ad_group_id IS NULL
            AND daily_metrics.ad_id IS NULL
            AND daily_metrics.device IS NULL
            AND daily_metrics.publisher_platform IS NULL
            AND daily_metrics.age_range IS NULL
            AND daily_metrics.region IS NULL
        WHERE clients.slug = %s AND campaigns.objective = ANY(%s)
        """,
        (start, end, client_slug, objectives),
    )

    action_row = fetch_one(
        connection,
        """
        SELECT
            COALESCE(SUM(daily_actions.count), 0) AS count,
            COALESCE(SUM(daily_actions.value), 0) AS value
        FROM daily_actions
        INNER JOIN campaigns ON campaigns.id = daily_actions.campaign_id
        INNER JOIN ad_accounts ON ad_accounts.id = campaigns.ad_account_id
        INNER JOIN clients ON clients.id = ad_accounts.client_id
        WHERE clients.slug = %s
          AND campaigns.objective = ANY(%s)
          AND daily_actions.action_type = ANY(%s)
          AND daily_actions.metric_date BETWEEN %s AND %s
          AND daily_actions.ad_group_id IS NULL
          AND daily_actions.ad_id IS NULL
          AND daily_actions.age_range IS NULL
          AND daily_actions.region IS NULL
          AND daily_actions.publisher_platform IS NULL
        """,
        (client_slug, objectives, block["action_types"], start, end),
    )

    spend = float(campaign_row["spend"] or 0)
    impressions = int(campaign_row["impressions"] or 0)
    reach = int(campaign_row["reach"] or 0)
    count = float(action_row["count"] or 0)
    value = float(action_row["value"] or 0)

    sub_metrics = []
    for sub in block.get("sub_metrics", []):
        sub_row = fetch_one(
            connection,
            """
            SELECT COALESCE(SUM(daily_actions.count), 0) AS count
            FROM daily_actions
            INNER JOIN campaigns ON campaigns.id = daily_actions.campaign_id
            INNER JOIN ad_accounts ON ad_accounts.id = campaigns.ad_account_id
            INNER JOIN clients ON clients.id = ad_accounts.client_id
            WHERE clients.slug = %s
              AND campaigns.objective = ANY(%s)
              AND daily_actions.action_type = ANY(%s)
              AND daily_actions.metric_date BETWEEN %s AND %s
              AND daily_actions.ad_group_id IS NULL
              AND daily_actions.ad_id IS NULL
              AND daily_actions.age_range IS NULL
              AND daily_actions.region IS NULL
              AND daily_actions.publisher_platform IS NULL
            """,
            (client_slug, objectives, sub["action_types"], start, end),
        )
        sub_metrics.append(
            {"label": sub["label"], "count": float(sub_row["count"] or 0)}
        )

    return {
        "key": block_key,
        "label": block["label"],
        "count_label": block["count_label"],
        "cost_label": block["cost_label"],
        "spend": spend,
        "reach": reach,
        "frequency": (impressions / reach) if reach else 0,
        "count": count,
        "value": value,
        "cost_per": (spend / count) if count else 0,
        "roas": (value / spend) if spend else 0,
        "sub_metrics": sub_metrics,
        "show_reach_frequency": block.get("show_reach_frequency", False),
        "show_value_and_roas": block.get("show_value_and_roas", False),
        "has_data": bool(count or spend),
    }


def detect_available_blocks(connection, client_slug: str, start: date, end: date) -> list[str]:
    """Blocos com pelo menos uma campanha com investimento no período —
    usado quando o pedido de relatório não especifica blocos (ex: CLI
    de teste), pra não forçar quem chama a listar todos manualmente."""

    rows = fetch_all(
        connection,
        """
        SELECT DISTINCT campaigns.objective
        FROM campaigns
        INNER JOIN ad_accounts ON ad_accounts.id = campaigns.ad_account_id
        INNER JOIN clients ON clients.id = ad_accounts.client_id
        INNER JOIN daily_metrics
            ON daily_metrics.campaign_id = campaigns.id
            AND daily_metrics.metric_date BETWEEN %s AND %s
            AND daily_metrics.ad_group_id IS NULL
            AND daily_metrics.ad_id IS NULL
            AND daily_metrics.device IS NULL
            AND daily_metrics.publisher_platform IS NULL
            AND daily_metrics.age_range IS NULL
            AND daily_metrics.region IS NULL
            AND daily_metrics.spend > 0
        WHERE clients.slug = %s
        """,
        (start, end, client_slug),
    )

    found = {OBJECTIVE_TO_BLOCK[r["objective"]] for r in rows if r["objective"] in OBJECTIVE_TO_BLOCK}
    return [key for key in BLOCKS if key in found]


def get_daily_trend(connection, client_slug: str, start: date, end: date) -> list[dict]:
    return fetch_all(
        connection,
        """
        SELECT
            daily_metrics.metric_date,
            SUM(daily_metrics.impressions) AS impressions,
            SUM(daily_metrics.clicks) AS clicks,
            SUM(daily_metrics.spend) AS spend,
            SUM(daily_metrics.reach) AS reach
        FROM daily_metrics
        INNER JOIN campaigns ON campaigns.id = daily_metrics.campaign_id
        INNER JOIN ad_accounts ON ad_accounts.id = campaigns.ad_account_id
        INNER JOIN clients ON clients.id = ad_accounts.client_id
        WHERE clients.slug = %s
          AND daily_metrics.metric_date BETWEEN %s AND %s
          AND daily_metrics.ad_group_id IS NULL
          AND daily_metrics.ad_id IS NULL
          AND daily_metrics.device IS NULL
          AND daily_metrics.publisher_platform IS NULL
          AND daily_metrics.age_range IS NULL
          AND daily_metrics.region IS NULL
        GROUP BY daily_metrics.metric_date
        ORDER BY daily_metrics.metric_date
        """,
        (client_slug, start, end),
    )


def get_platform_breakdown(connection, client_slug: str, start: date, end: date) -> list[dict]:
    """Agregado por publisher_platform (facebook/instagram/messenger/
    audience_network/threads) — usa o breakdown dedicado só de
    publisher_platform que o sync grava desde a migration 0004
    (`device IS NULL` aqui filtra especificamente essas linhas,
    diferentes das linhas mais antigas que combinam device+plataforma
    pro AI tool get_campaign_device_breakdown).

    Esse breakdown dedicado devolve reach/actions utilizáveis
    (confirmado empiricamente, diferente da combinação com device),
    então alcance/frequência/leads por plataforma entram aqui."""

    rows = fetch_all(
        connection,
        """
        SELECT
            daily_metrics.publisher_platform AS platform,
            COALESCE(SUM(daily_metrics.spend), 0) AS spend,
            COALESCE(SUM(daily_metrics.impressions), 0) AS impressions,
            COALESCE(SUM(daily_metrics.reach), 0) AS reach,
            COALESCE(SUM(daily_metrics.clicks), 0) AS clicks
        FROM daily_metrics
        INNER JOIN campaigns ON campaigns.id = daily_metrics.campaign_id
        INNER JOIN ad_accounts ON ad_accounts.id = campaigns.ad_account_id
        INNER JOIN clients ON clients.id = ad_accounts.client_id
        WHERE clients.slug = %s
          AND daily_metrics.metric_date BETWEEN %s AND %s
          AND daily_metrics.publisher_platform IS NOT NULL
          AND daily_metrics.device IS NULL
          AND daily_metrics.ad_group_id IS NULL
          AND daily_metrics.ad_id IS NULL
        GROUP BY daily_metrics.publisher_platform
        HAVING COALESCE(SUM(daily_metrics.spend), 0) > 0
        ORDER BY spend DESC
        """,
        (client_slug, start, end),
    )

    lead_rows = fetch_all(
        connection,
        """
        SELECT daily_actions.publisher_platform, COALESCE(SUM(daily_actions.count), 0) AS leads
        FROM daily_actions
        INNER JOIN campaigns ON campaigns.id = daily_actions.campaign_id
        INNER JOIN ad_accounts ON ad_accounts.id = campaigns.ad_account_id
        INNER JOIN clients ON clients.id = ad_accounts.client_id
        WHERE clients.slug = %s
          AND daily_actions.metric_date BETWEEN %s AND %s
          AND daily_actions.publisher_platform IS NOT NULL
          AND daily_actions.action_type = 'lead'
        GROUP BY daily_actions.publisher_platform
        """,
        (client_slug, start, end),
    )
    leads_by_platform = {r["publisher_platform"]: float(r["leads"] or 0) for r in lead_rows}

    result = []
    for row in rows:
        spend = float(row["spend"] or 0)
        impressions = int(row["impressions"] or 0)
        reach = int(row["reach"] or 0)
        clicks = int(row["clicks"] or 0)
        result.append(
            {
                "platform": row["platform"],
                "spend": spend,
                "impressions": impressions,
                "reach": reach,
                "frequency": (impressions / reach) if reach else 0,
                "clicks": clicks,
                "cpm": (spend / impressions * 1000) if impressions else 0,
                "cpc": (spend / clicks) if clicks else 0,
                "leads": leads_by_platform.get(row["platform"], 0),
            }
        )
    return result


def get_demographics_breakdown(connection, client_slug: str, start: date, end: date) -> dict:
    """Faixa etária + gênero, a partir do breakdown age+gender que o
    sync grava desde a Fase 2 (migration 0002). Diferente da seção de
    plataforma, aqui dá pra contar leads por faixa/gênero porque
    daily_actions também tem essas colunas — ver
    src.integrations.meta_ads.sync.sync_demographics_breakdown."""

    rows = fetch_all(
        connection,
        """
        SELECT
            daily_metrics.age_range,
            daily_metrics.gender,
            COALESCE(SUM(daily_metrics.spend), 0) AS spend,
            COALESCE(SUM(daily_metrics.reach), 0) AS reach,
            COALESCE(SUM(daily_metrics.clicks), 0) AS clicks
        FROM daily_metrics
        INNER JOIN campaigns ON campaigns.id = daily_metrics.campaign_id
        INNER JOIN ad_accounts ON ad_accounts.id = campaigns.ad_account_id
        INNER JOIN clients ON clients.id = ad_accounts.client_id
        WHERE clients.slug = %s
          AND daily_metrics.metric_date BETWEEN %s AND %s
          AND daily_metrics.age_range IS NOT NULL
        GROUP BY daily_metrics.age_range, daily_metrics.gender
        HAVING COALESCE(SUM(daily_metrics.spend), 0) > 0
        """,
        (client_slug, start, end),
    )

    lead_rows = fetch_all(
        connection,
        """
        SELECT daily_actions.age_range, daily_actions.gender, COALESCE(SUM(daily_actions.count), 0) AS leads
        FROM daily_actions
        INNER JOIN campaigns ON campaigns.id = daily_actions.campaign_id
        INNER JOIN ad_accounts ON ad_accounts.id = campaigns.ad_account_id
        INNER JOIN clients ON clients.id = ad_accounts.client_id
        WHERE clients.slug = %s
          AND daily_actions.metric_date BETWEEN %s AND %s
          AND daily_actions.age_range IS NOT NULL
          AND daily_actions.action_type = 'lead'
        GROUP BY daily_actions.age_range, daily_actions.gender
        """,
        (client_slug, start, end),
    )
    leads_by_combo = {(r["age_range"], r["gender"]): float(r["leads"] or 0) for r in lead_rows}

    table = []
    by_age: dict[str, dict] = {}
    by_gender: dict[str, dict] = {}
    for row in rows:
        age_range = row["age_range"]
        gender = row["gender"]
        spend = float(row["spend"] or 0)
        reach = int(row["reach"] or 0)
        clicks = int(row["clicks"] or 0)
        leads = leads_by_combo.get((age_range, gender), 0)

        table.append(
            {
                "age_range": age_range,
                "gender": gender,
                "spend": spend,
                "reach": reach,
                "clicks": clicks,
                "leads": leads,
            }
        )

        age_bucket = by_age.setdefault(age_range, {"age_range": age_range, "clicks": 0, "leads": 0})
        age_bucket["clicks"] += clicks
        age_bucket["leads"] += leads

        gender_bucket = by_gender.setdefault(gender, {"gender": gender, "leads": 0})
        gender_bucket["leads"] += leads

    def _age_sort_key(item: dict) -> int:
        try:
            return AGE_RANGE_ORDER.index(item["age_range"])
        except ValueError:
            return len(AGE_RANGE_ORDER)

    table.sort(key=lambda r: r["spend"], reverse=True)

    return {
        "table": table,
        "by_age": sorted(by_age.values(), key=_age_sort_key),
        "by_gender": sorted(by_gender.values(), key=lambda r: r["leads"], reverse=True),
    }


def get_region_breakdown(connection, client_slug: str, start: date, end: date) -> list[dict]:
    """Regiões com maior alcance, a partir do breakdown region que o
    sync grava desde a Fase 2 (migration 0002) — mesma ideia de
    get_demographics_breakdown, com leads por região."""

    rows = fetch_all(
        connection,
        """
        SELECT
            daily_metrics.region,
            COALESCE(SUM(daily_metrics.reach), 0) AS reach,
            COALESCE(SUM(daily_metrics.impressions), 0) AS impressions,
            COALESCE(SUM(daily_metrics.spend), 0) AS spend
        FROM daily_metrics
        INNER JOIN campaigns ON campaigns.id = daily_metrics.campaign_id
        INNER JOIN ad_accounts ON ad_accounts.id = campaigns.ad_account_id
        INNER JOIN clients ON clients.id = ad_accounts.client_id
        WHERE clients.slug = %s
          AND daily_metrics.metric_date BETWEEN %s AND %s
          AND daily_metrics.region IS NOT NULL
        GROUP BY daily_metrics.region
        HAVING COALESCE(SUM(daily_metrics.spend), 0) > 0
        ORDER BY reach DESC
        """,
        (client_slug, start, end),
    )

    lead_rows = fetch_all(
        connection,
        """
        SELECT daily_actions.region, COALESCE(SUM(daily_actions.count), 0) AS leads
        FROM daily_actions
        INNER JOIN campaigns ON campaigns.id = daily_actions.campaign_id
        INNER JOIN ad_accounts ON ad_accounts.id = campaigns.ad_account_id
        INNER JOIN clients ON clients.id = ad_accounts.client_id
        WHERE clients.slug = %s
          AND daily_actions.metric_date BETWEEN %s AND %s
          AND daily_actions.region IS NOT NULL
          AND daily_actions.action_type = 'lead'
        GROUP BY daily_actions.region
        """,
        (client_slug, start, end),
    )
    leads_by_region = {r["region"]: float(r["leads"] or 0) for r in lead_rows}

    result = []
    for row in rows:
        reach = int(row["reach"] or 0)
        impressions = int(row["impressions"] or 0)
        spend = float(row["spend"] or 0)
        result.append(
            {
                "region": row["region"],
                "reach": reach,
                "impressions": impressions,
                "frequency": (impressions / reach) if reach else 0,
                "spend": spend,
                "cpm": (spend / impressions * 1000) if impressions else 0,
                "leads": leads_by_region.get(row["region"], 0),
            }
        )
    return result


def detect_available_extra_sections(connection, client_slug: str, start: date, end: date) -> list[str]:
    """Mesma lógica de detect_available_blocks, mas pras seções
    transversais — usada quando o pedido de relatório não especifica
    quais seções extras incluir."""

    available = []
    if get_platform_breakdown(connection, client_slug, start, end):
        available.append(PLATAFORMA)
    if get_top_campaigns(connection, client_slug, start, end):
        available.append(CAMPANHAS)
    if get_demographics_breakdown(connection, client_slug, start, end)["table"]:
        available.append(DEMOGRAFIA)
    if get_region_breakdown(connection, client_slug, start, end):
        available.append(REGIAO)
    if get_top_ads(connection, client_slug, start, end):
        available.append(ANUNCIOS)
    return available


def get_top_campaigns(connection, client_slug: str, start: date, end: date, limit: int = 10) -> list[dict]:
    rows = fetch_all(
        connection,
        """
        SELECT
            campaigns.id,
            campaigns.name,
            campaigns.status,
            COALESCE(SUM(daily_metrics.impressions), 0) AS impressions,
            COALESCE(SUM(daily_metrics.reach), 0) AS reach,
            COALESCE(SUM(daily_metrics.clicks), 0) AS clicks,
            COALESCE(SUM(daily_metrics.spend), 0) AS spend
        FROM campaigns
        INNER JOIN ad_accounts ON ad_accounts.id = campaigns.ad_account_id
        INNER JOIN clients ON clients.id = ad_accounts.client_id
        LEFT JOIN daily_metrics
            ON daily_metrics.campaign_id = campaigns.id
            AND daily_metrics.metric_date BETWEEN %s AND %s
            AND daily_metrics.ad_group_id IS NULL
            AND daily_metrics.ad_id IS NULL
            AND daily_metrics.device IS NULL
            AND daily_metrics.publisher_platform IS NULL
            AND daily_metrics.age_range IS NULL
            AND daily_metrics.region IS NULL
        WHERE clients.slug = %s
        GROUP BY campaigns.id, campaigns.name, campaigns.status
        HAVING COALESCE(SUM(daily_metrics.spend), 0) > 0
        ORDER BY spend DESC
        LIMIT %s
        """,
        (start, end, client_slug, limit),
    )

    if not rows:
        return []

    campaign_ids = [r["id"] for r in rows]
    lead_rows = fetch_all(
        connection,
        """
        SELECT daily_actions.campaign_id, COALESCE(SUM(daily_actions.count), 0) AS leads
        FROM daily_actions
        WHERE daily_actions.campaign_id = ANY(%s)
          AND daily_actions.ad_group_id IS NULL
          AND daily_actions.ad_id IS NULL
          AND daily_actions.age_range IS NULL
          AND daily_actions.region IS NULL
          AND daily_actions.publisher_platform IS NULL
          AND daily_actions.metric_date BETWEEN %s AND %s
          AND daily_actions.action_type = 'lead'
        GROUP BY daily_actions.campaign_id
        """,
        (campaign_ids, start, end),
    )
    leads_by_campaign = {r["campaign_id"]: float(r["leads"] or 0) for r in lead_rows}

    result = []
    for row in rows:
        spend = float(row["spend"] or 0)
        impressions = int(row["impressions"] or 0)
        reach = int(row["reach"] or 0)
        clicks = int(row["clicks"] or 0)
        result.append(
            {
                "name": row["name"],
                "status": row["status"],
                "spend": spend,
                "impressions": impressions,
                "reach": reach,
                "frequency": (impressions / reach) if reach else 0,
                "clicks": clicks,
                "cpc": (spend / clicks) if clicks else 0,
                "cpm": (spend / impressions * 1000) if impressions else 0,
                "leads": leads_by_campaign.get(row["id"], 0),
            }
        )
    return result


def get_top_ads(connection, client_slug: str, start: date, end: date, limit: int = 10) -> list[dict]:
    """Anúncios individuais com mais investimento, com a miniatura do
    criativo (`ads.creative_thumbnail_url`) — grão mais fino que
    get_top_campaigns, alimentado por
    src.integrations.meta_ads.sync.sync_ad_insights_and_actions
    (Fase 3). A miniatura é uma URL assinada da Meta com expiração
    embutida (ver migration 0003) — pode quebrar pra relatório de
    período muito antigo, gerado bem depois do último sync do anúncio."""

    rows = fetch_all(
        connection,
        """
        SELECT
            ads.id,
            ads.name,
            ads.status,
            ads.creative_thumbnail_url,
            COALESCE(SUM(daily_metrics.spend), 0) AS spend,
            COALESCE(SUM(daily_metrics.impressions), 0) AS impressions,
            COALESCE(SUM(daily_metrics.reach), 0) AS reach,
            COALESCE(SUM(daily_metrics.clicks), 0) AS clicks
        FROM ads
        INNER JOIN ad_groups ON ad_groups.id = ads.ad_group_id
        INNER JOIN campaigns ON campaigns.id = ad_groups.campaign_id
        INNER JOIN ad_accounts ON ad_accounts.id = campaigns.ad_account_id
        INNER JOIN clients ON clients.id = ad_accounts.client_id
        INNER JOIN daily_metrics
            ON daily_metrics.ad_id = ads.id
            AND daily_metrics.metric_date BETWEEN %s AND %s
            AND daily_metrics.device IS NULL
            AND daily_metrics.publisher_platform IS NULL
        WHERE clients.slug = %s
        GROUP BY ads.id, ads.name, ads.status, ads.creative_thumbnail_url
        HAVING COALESCE(SUM(daily_metrics.spend), 0) > 0
        ORDER BY spend DESC
        LIMIT %s
        """,
        (start, end, client_slug, limit),
    )

    if not rows:
        return []

    ad_ids = [r["id"] for r in rows]
    lead_rows = fetch_all(
        connection,
        """
        SELECT daily_actions.ad_id, COALESCE(SUM(daily_actions.count), 0) AS leads
        FROM daily_actions
        WHERE daily_actions.ad_id = ANY(%s)
          AND daily_actions.metric_date BETWEEN %s AND %s
          AND daily_actions.action_type = 'lead'
        GROUP BY daily_actions.ad_id
        """,
        (ad_ids, start, end),
    )
    leads_by_ad = {r["ad_id"]: float(r["leads"] or 0) for r in lead_rows}

    result = []
    for row in rows:
        spend = float(row["spend"] or 0)
        impressions = int(row["impressions"] or 0)
        reach = int(row["reach"] or 0)
        clicks = int(row["clicks"] or 0)
        result.append(
            {
                "name": row["name"],
                "status": row["status"],
                "thumbnail_url": row["creative_thumbnail_url"],
                "spend": spend,
                "impressions": impressions,
                "reach": reach,
                "frequency": (impressions / reach) if reach else 0,
                "clicks": clicks,
                "cpc": (spend / clicks) if clicks else 0,
                "cpm": (spend / impressions * 1000) if impressions else 0,
                "leads": leads_by_ad.get(row["id"], 0),
            }
        )
    return result


def load_report_data(
    client_slug: str,
    start: date,
    end: date,
    blocks: list[str] | None = None,
    extra: list[str] | None = None,
    drop_empty: bool = False,
) -> dict:
    """drop_empty=True remove do relatório os blocos/seções extras
    pedidos que não tiverem dado real no período, em vez de deixá-los
    aparecer como seção "sem dado" — usado pelo caminho da IA (que não
    tem como saber de antemão quais blocos o cliente realmente tem,
    diferente do dashboard, onde a pessoa já vê isso nos checkboxes
    antes de pedir). Os itens descartados voltam em `excluded_blocks`/
    `excluded_extra`, pra quem chamou poder avisar o motivo pro
    usuário.

    `extra` segue o mesmo vocabulário de `blocks`, mas pras seções
    transversais definidas em sections.py (plataforma, campanhas) —
    ver EXTRA_SECTIONS."""

    with get_connection() as connection:
        client = get_client(connection, client_slug)
        if client is None:
            raise ValueError(f"Cliente não encontrado: {client_slug}")

        if blocks is None:
            blocks = detect_available_blocks(connection, client_slug, start, end)

        unknown = [key for key in blocks if key not in BLOCKS]
        if unknown:
            raise ValueError(f"Bloco(s) desconhecido(s): {', '.join(unknown)}")

        if extra is None:
            extra = detect_available_extra_sections(connection, client_slug, start, end)

        unknown_extra = [key for key in extra if key not in EXTRA_SECTIONS]
        if unknown_extra:
            raise ValueError(f"Seção(ões) desconhecida(s): {', '.join(unknown_extra)}")

        block_results = [
            get_block_data(connection, client_slug, start, end, key) for key in blocks
        ]

        if drop_empty:
            included = [b for b in block_results if b["has_data"]]
            excluded = [b for b in block_results if not b["has_data"]]
        else:
            included = block_results
            excluded = []

        platform_breakdown = (
            get_platform_breakdown(connection, client_slug, start, end)
            if PLATAFORMA in extra
            else []
        )
        top_campaigns = (
            get_top_campaigns(connection, client_slug, start, end)
            if CAMPANHAS in extra
            else []
        )
        demographics = (
            get_demographics_breakdown(connection, client_slug, start, end)
            if DEMOGRAFIA in extra
            else None
        )
        region_breakdown = (
            get_region_breakdown(connection, client_slug, start, end)
            if REGIAO in extra
            else []
        )
        top_ads = (
            get_top_ads(connection, client_slug, start, end)
            if ANUNCIOS in extra
            else []
        )
        extra_has_data = {
            PLATAFORMA: bool(platform_breakdown),
            CAMPANHAS: bool(top_campaigns),
            DEMOGRAFIA: bool(demographics and demographics["table"]),
            REGIAO: bool(region_breakdown),
            ANUNCIOS: bool(top_ads),
        }

        included_extra = [
            {"key": key, "label": EXTRA_SECTIONS[key]["label"]}
            for key in extra
            if extra_has_data[key] or not drop_empty
        ]
        excluded_extra = [
            {"key": key, "label": EXTRA_SECTIONS[key]["label"]}
            for key in extra
            if not extra_has_data[key] and drop_empty
        ]
        shown_extra = {e["key"] for e in included_extra}

        return {
            "client": client,
            "period": {"start": start, "end": end},
            "summary": get_summary(connection, client_slug, start, end),
            "daily_trend": get_daily_trend(connection, client_slug, start, end),
            "blocks": included,
            "excluded_blocks": excluded,
            "show_platform": PLATAFORMA in shown_extra,
            "platform_breakdown": platform_breakdown if PLATAFORMA in shown_extra else [],
            "show_campaigns": CAMPANHAS in shown_extra,
            "top_campaigns": top_campaigns if CAMPANHAS in shown_extra else [],
            "show_demographics": DEMOGRAFIA in shown_extra,
            "demographics": demographics if DEMOGRAFIA in shown_extra else None,
            "show_region": REGIAO in shown_extra,
            "region_breakdown": region_breakdown if REGIAO in shown_extra else [],
            "show_ads": ANUNCIOS in shown_extra,
            "top_ads": top_ads if ANUNCIOS in shown_extra else [],
            "included_extra": included_extra,
            "excluded_extra": excluded_extra,
        }
