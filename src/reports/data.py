"""Consultas de dados para o gerador de relatório em PDF.

Camada somente leitura — usa as mesmas credenciais restritas
(sync_ai, via src.ai_tools.db) que as ferramentas de IA, não as
credenciais administrativas. Um relatório não deveria conseguir
escrever no banco.

As agregações seguem a mesma regra de grão já usada em
src/ai_tools/*.py: só soma linhas com ad_group_id/ad_id/device/
publisher_platform nulos, para não contar a mesma métrica duas
vezes quando existir dado mais granular para a mesma campanha/data.
"""

from __future__ import annotations

from datetime import date

from src.ai_tools.db import fetch_all, fetch_one, get_connection


def get_client(connection, client_slug: str) -> dict | None:
    return fetch_one(
        connection,
        "SELECT id, name, slug, industry FROM clients WHERE slug = %s LIMIT 1",
        (client_slug,),
    )


def get_summary(connection, client_slug: str, start: date, end: date) -> dict:
    row = fetch_one(
        connection,
        """
        SELECT
            COALESCE(SUM(daily_metrics.impressions), 0) AS impressions,
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
        WHERE clients.slug = %s
        """,
        (start, end, client_slug),
    )

    impressions = int(row["impressions"] or 0)
    clicks = int(row["clicks"] or 0)
    spend = float(row["spend"] or 0)

    return {
        "impressions": impressions,
        "clicks": clicks,
        "spend": spend,
        "ctr_percent": (clicks / impressions * 100) if impressions else 0,
        "cpc": (spend / clicks) if clicks else 0,
        "cpm": (spend / impressions * 1000) if impressions else 0,
    }


def get_daily_trend(connection, client_slug: str, start: date, end: date) -> list[dict]:
    return fetch_all(
        connection,
        """
        SELECT
            daily_metrics.metric_date,
            SUM(daily_metrics.impressions) AS impressions,
            SUM(daily_metrics.clicks) AS clicks,
            SUM(daily_metrics.spend) AS spend
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
        GROUP BY daily_metrics.metric_date
        ORDER BY daily_metrics.metric_date
        """,
        (client_slug, start, end),
    )


def get_actions_summary(connection, client_slug: str, start: date, end: date) -> list[dict]:
    rows = fetch_all(
        connection,
        """
        SELECT
            action_type_catalog.business_category,
            COALESCE(SUM(daily_actions.count), 0) AS total_count
        FROM action_type_catalog
        LEFT JOIN daily_actions
            ON daily_actions.action_type = action_type_catalog.action_type
            AND daily_actions.ad_group_id IS NULL
            AND daily_actions.ad_id IS NULL
            AND daily_actions.metric_date BETWEEN %s AND %s
            AND daily_actions.campaign_id IN (
                SELECT campaigns.id
                FROM campaigns
                INNER JOIN ad_accounts ON ad_accounts.id = campaigns.ad_account_id
                INNER JOIN clients ON clients.id = ad_accounts.client_id
                WHERE clients.slug = %s
            )
        WHERE action_type_catalog.is_canonical = true
        GROUP BY action_type_catalog.business_category
        ORDER BY total_count DESC
        """,
        (start, end, client_slug),
    )
    return [r for r in rows if float(r["total_count"] or 0) > 0]


def get_top_campaigns(connection, client_slug: str, start: date, end: date, limit: int = 10) -> list[dict]:
    return fetch_all(
        connection,
        """
        SELECT
            campaigns.name,
            campaigns.status,
            COALESCE(SUM(daily_metrics.impressions), 0) AS impressions,
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
        WHERE clients.slug = %s
        GROUP BY campaigns.id, campaigns.name, campaigns.status
        HAVING COALESCE(SUM(daily_metrics.spend), 0) > 0
        ORDER BY spend DESC
        LIMIT %s
        """,
        (start, end, client_slug, limit),
    )


def load_report_data(client_slug: str, start: date, end: date) -> dict:
    with get_connection() as connection:
        client = get_client(connection, client_slug)
        if client is None:
            raise ValueError(f"Cliente não encontrado: {client_slug}")

        return {
            "client": client,
            "period": {"start": start, "end": end},
            "summary": get_summary(connection, client_slug, start, end),
            "daily_trend": get_daily_trend(connection, client_slug, start, end),
            "actions": get_actions_summary(connection, client_slug, start, end),
            "top_campaigns": get_top_campaigns(connection, client_slug, start, end),
        }
