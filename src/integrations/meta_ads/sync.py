"""Sincronização real Meta Ads -> PostgreSQL.

Camada ADMINISTRATIVA — usa credenciais de escrita (.env.admin,
usuário sync_admin), nunca as credenciais somente-leitura da IA. Não
é uma ferramenta do catálogo de `AI_GUIDE.md`; roda como job
agendado ou manualmente por quem administra o projeto.

Uso manual:

    python -m src.integrations.meta_ads.sync --days 7
    python -m src.integrations.meta_ads.sync --days 7 --only hospital-de-olhos-videira

Cada execução, por conta, fica registrada em `data_sync_runs`
(status, quantidade de registros, erro se houver) — é o jeito de
confirmar depois que o agendador diário rodou de verdade.

Grão gravado, para bater com o que as ferramentas de IA esperam
(ver src/ai_tools/get_campaign_performance.py e docs/meta-ads-api-
exploracao.md):

- daily_metrics: uma passada no grão campanha (ad_group_id/ad_id/
  device/publisher_platform nulos) + uma passada no grão
  device+publisher_platform (ad_group_id/ad_id continuam nulos —
  ainda não sincronizamos no nível de anúncio individual).
- daily_actions: só no grão campanha. Todo action_type novo é
  registrado em action_type_catalog automaticamente (is_canonical
  = false, business_category = NULL) antes de gravar a ação — nunca
  falha a sincronização por causa de um action_type nunca visto.

Cuidado de unidade monetária (documentado porque é fácil errar):
`daily_budget`/`lifetime_budget` de ad set vêm da API na unidade
mínima da moeda (centavos) — dividimos por 100. `spend` de insights
já vem em unidade decimal normal — não dividir de novo.
"""

from __future__ import annotations

import argparse
import sys
import traceback
from datetime import date, datetime, timedelta, timezone
from typing import Any

from src.db.admin import get_connection
from src.integrations.meta_ads.accounts import ACCOUNTS, AccountConfig
from src.integrations.meta_ads.client import MetaAdsAPIError, get_all_pages

DEFAULT_SYNC_DAYS = 7


# ============================================================
# Hierarquia (organization / client / ad_account)
# ============================================================

def ensure_hierarchy(cursor, account: AccountConfig) -> dict[str, int]:
    cursor.execute(
        """
        INSERT INTO organizations (slug, name)
        VALUES (%s, %s)
        ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name
        RETURNING id
        """,
        (account.organization_slug, account.organization_name),
    )
    organization_id = cursor.fetchone()["id"]

    cursor.execute(
        """
        INSERT INTO clients (organization_id, slug, name, industry)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (organization_id, slug)
        DO UPDATE SET name = EXCLUDED.name, industry = EXCLUDED.industry
        RETURNING id
        """,
        (organization_id, account.client_slug, account.client_name, account.client_industry),
    )
    client_id = cursor.fetchone()["id"]

    cursor.execute("SELECT id FROM platforms WHERE slug = 'meta_ads'")
    platform_id = cursor.fetchone()["id"]

    cursor.execute(
        """
        INSERT INTO ad_accounts (client_id, platform_id, external_account_id, name, currency)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (platform_id, external_account_id)
        DO UPDATE SET name = EXCLUDED.name
        RETURNING id
        """,
        (client_id, platform_id, account.external_account_id, account.client_name, "BRL"),
    )
    ad_account_id = cursor.fetchone()["id"]

    return {
        "organization_id": organization_id,
        "client_id": client_id,
        "ad_account_id": ad_account_id,
    }


# ============================================================
# Entidades (campaigns / ad_groups / ads)
# ============================================================

def sync_campaigns(cursor, ad_account_db_id: int, external_account_id: str) -> dict[str, int]:
    campaign_map: dict[str, int] = {}

    for item in get_all_pages(
        f"{external_account_id}/campaigns",
        {"fields": "id,name,objective,effective_status", "limit": 100},
    ):
        cursor.execute(
            """
            INSERT INTO campaigns (ad_account_id, external_campaign_id, name, objective, status)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (ad_account_id, external_campaign_id)
            DO UPDATE SET name = EXCLUDED.name, objective = EXCLUDED.objective, status = EXCLUDED.status
            RETURNING id
            """,
            (
                ad_account_db_id,
                item["id"],
                item.get("name"),
                item.get("objective"),
                item.get("effective_status"),
            ),
        )
        campaign_map[item["id"]] = cursor.fetchone()["id"]

    return campaign_map


def _minor_to_major(raw: str | None) -> float | None:
    if raw is None:
        return None
    value = float(raw)
    return None if value == 0 else round(value / 100, 2)


def sync_ad_groups(cursor, campaign_map: dict[str, int], external_account_id: str) -> dict[str, int]:
    ad_group_map: dict[str, int] = {}

    for item in get_all_pages(
        f"{external_account_id}/adsets",
        {
            "fields": "id,name,campaign_id,effective_status,optimization_goal,daily_budget,lifetime_budget",
            "limit": 100,
        },
    ):
        campaign_db_id = campaign_map.get(item.get("campaign_id"))
        if campaign_db_id is None:
            # Ad set de uma campanha que não veio na listagem de
            # campaigns (não deveria acontecer, mas não deve derrubar
            # a sincronização inteira por causa de uma inconsistência).
            continue

        cursor.execute(
            """
            INSERT INTO ad_groups
                (campaign_id, external_ad_group_id, name, status, optimization_goal, daily_budget, lifetime_budget)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (campaign_id, external_ad_group_id)
            DO UPDATE SET
                name = EXCLUDED.name,
                status = EXCLUDED.status,
                optimization_goal = EXCLUDED.optimization_goal,
                daily_budget = EXCLUDED.daily_budget,
                lifetime_budget = EXCLUDED.lifetime_budget
            RETURNING id
            """,
            (
                campaign_db_id,
                item["id"],
                item.get("name"),
                item.get("effective_status"),
                item.get("optimization_goal"),
                _minor_to_major(item.get("daily_budget")),
                _minor_to_major(item.get("lifetime_budget")),
            ),
        )
        ad_group_map[item["id"]] = cursor.fetchone()["id"]

    return ad_group_map


def sync_ads(cursor, ad_group_map: dict[str, int], external_account_id: str) -> int:
    count = 0

    for item in get_all_pages(
        f"{external_account_id}/ads",
        {"fields": "id,name,adset_id,effective_status,creative{object_type}", "limit": 100},
    ):
        ad_group_db_id = ad_group_map.get(item.get("adset_id"))
        if ad_group_db_id is None:
            continue

        name = item.get("name") or None
        creative_type = (item.get("creative") or {}).get("object_type")

        cursor.execute(
            """
            INSERT INTO ads (ad_group_id, external_ad_id, name, creative_type, status)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (ad_group_id, external_ad_id)
            DO UPDATE SET name = EXCLUDED.name, creative_type = EXCLUDED.creative_type, status = EXCLUDED.status
            """,
            (ad_group_db_id, item["id"], name, creative_type, item.get("effective_status")),
        )
        count += 1

    return count


# ============================================================
# Métricas e ações
# ============================================================

CHUNK_DAYS = 30


def _date_chunks(since: date, until: date, chunk_days: int = CHUNK_DAYS):
    """Quebra [since, until] em janelas menores.

    Pedir métricas diárias (time_increment=1) pro nível de campanha
    numa conta com centenas de campanhas, numa janela grande de uma
    vez só, já deu timeout na exploração (ver docs/meta-ads-api-
    exploracao.md, item 4). Backfills maiores que ~30 dias usam isso
    pra manter cada chamada à API num tamanho seguro.
    """

    chunk_start = since
    while chunk_start <= until:
        chunk_end = min(chunk_start + timedelta(days=chunk_days - 1), until)
        yield chunk_start, chunk_end
        chunk_start = chunk_end + timedelta(days=1)


def ensure_action_types(cursor, action_types: set[str]) -> None:
    if not action_types:
        return

    cursor.execute("SELECT id FROM platforms WHERE slug = 'meta_ads'")
    platform_id = cursor.fetchone()["id"]

    for action_type in action_types:
        cursor.execute(
            """
            INSERT INTO action_type_catalog (action_type, platform_id, is_canonical)
            VALUES (%s, %s, false)
            ON CONFLICT (action_type) DO NOTHING
            """,
            (action_type, platform_id),
        )


def sync_insights_and_actions(
    cursor,
    campaign_map: dict[str, int],
    external_account_id: str,
    since: date,
    until: date,
) -> tuple[int, int]:
    metrics_rows = 0
    action_rows: list[tuple] = []
    seen_action_types: set[str] = set()

    for chunk_since, chunk_until in _date_chunks(since, until):
        for item in get_all_pages(
            f"{external_account_id}/insights",
            {
                "level": "campaign",
                "time_increment": 1,
                "time_range": f'{{"since":"{chunk_since}","until":"{chunk_until}"}}',
                "fields": "campaign_id,date_start,impressions,clicks,spend,reach,frequency,actions,action_values",
                "limit": 200,
            },
        ):
            campaign_db_id = campaign_map.get(item.get("campaign_id"))
            if campaign_db_id is None:
                continue

            metric_date = item["date_start"]

            cursor.execute(
                """
                INSERT INTO daily_metrics (campaign_id, metric_date, impressions, clicks, spend, reach, frequency)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (campaign_id, ad_group_id, ad_id, metric_date, device, publisher_platform)
                DO UPDATE SET
                    impressions = EXCLUDED.impressions,
                    clicks = EXCLUDED.clicks,
                    spend = EXCLUDED.spend,
                    reach = EXCLUDED.reach,
                    frequency = EXCLUDED.frequency
                """,
                (
                    campaign_db_id,
                    metric_date,
                    int(item.get("impressions", 0) or 0),
                    int(item.get("clicks", 0) or 0),
                    float(item.get("spend", 0) or 0),
                    int(item.get("reach", 0) or 0) or None,
                    float(item.get("frequency", 0) or 0) or None,
                ),
            )
            metrics_rows += 1

            counts = {a["action_type"]: a.get("value") for a in item.get("actions", [])}
            values = {a["action_type"]: a.get("value") for a in item.get("action_values", [])}

            for action_type in set(counts) | set(values):
                seen_action_types.add(action_type)
                action_rows.append(
                    (
                        campaign_db_id,
                        metric_date,
                        action_type,
                        float(counts.get(action_type) or 0),
                        float(values[action_type]) if values.get(action_type) is not None else None,
                    )
                )

    ensure_action_types(cursor, seen_action_types)

    for row in action_rows:
        cursor.execute(
            """
            INSERT INTO daily_actions (campaign_id, metric_date, action_type, count, value)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (campaign_id, ad_group_id, ad_id, metric_date, action_type)
            DO UPDATE SET count = EXCLUDED.count, value = EXCLUDED.value
            """,
            row,
        )

    return metrics_rows, len(action_rows)


def sync_device_breakdown(
    cursor,
    campaign_map: dict[str, int],
    external_account_id: str,
    since: date,
    until: date,
) -> int:
    rows = 0

    for chunk_since, chunk_until in _date_chunks(since, until):
        for item in get_all_pages(
            f"{external_account_id}/insights",
            {
                "level": "campaign",
                "time_increment": 1,
                "time_range": f'{{"since":"{chunk_since}","until":"{chunk_until}"}}',
                "breakdowns": "publisher_platform,platform_position,impression_device",
                "fields": "campaign_id,date_start,impressions,clicks,spend",
                "limit": 200,
            },
        ):
            campaign_db_id = campaign_map.get(item.get("campaign_id"))
            if campaign_db_id is None:
                continue

            cursor.execute(
                """
                INSERT INTO daily_metrics (campaign_id, metric_date, device, publisher_platform, impressions, clicks, spend)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (campaign_id, ad_group_id, ad_id, metric_date, device, publisher_platform)
                DO UPDATE SET impressions = EXCLUDED.impressions, clicks = EXCLUDED.clicks, spend = EXCLUDED.spend
                """,
                (
                    campaign_db_id,
                    item["date_start"],
                    item.get("impression_device"),
                    item.get("publisher_platform"),
                    int(item.get("impressions", 0) or 0),
                    int(item.get("clicks", 0) or 0),
                    float(item.get("spend", 0) or 0),
                ),
            )
            rows += 1

    return rows


# ============================================================
# Orquestração
# ============================================================

def sync_account(account: AccountConfig, since: date, until: date) -> dict[str, Any]:
    started_at = datetime.now(timezone.utc)
    print(f"[{account.client_slug}] iniciando sincronização ({since} a {until})...")

    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            ids = ensure_hierarchy(cursor, account)
            external_account_id = account.external_account_id

            campaign_map = sync_campaigns(cursor, ids["ad_account_id"], external_account_id)
            ad_group_map = sync_ad_groups(cursor, campaign_map, external_account_id)
            ads_count = sync_ads(cursor, ad_group_map, external_account_id)

            metrics_rows, action_rows = sync_insights_and_actions(
                cursor, campaign_map, external_account_id, since, until
            )
            device_rows = sync_device_breakdown(
                cursor, campaign_map, external_account_id, since, until
            )

            total_records = (
                len(campaign_map) + len(ad_group_map) + ads_count
                + metrics_rows + action_rows + device_rows
            )

            cursor.execute(
                """
                INSERT INTO data_sync_runs
                    (ad_account_id, started_at, finished_at, status, records_processed)
                VALUES (%s, %s, %s, 'success', %s)
                """,
                (ids["ad_account_id"], started_at, datetime.now(timezone.utc), total_records),
            )
            conn.commit()

            print(
                f"[{account.client_slug}] OK — {len(campaign_map)} campanhas, "
                f"{len(ad_group_map)} ad sets, {ads_count} ads, {metrics_rows} linhas de métrica, "
                f"{action_rows} linhas de ação, {device_rows} linhas de device/plataforma."
            )

            return {"ok": True, "client_slug": account.client_slug, "records_processed": total_records}

        except Exception as exc:
            conn.rollback()
            error_message = f"{type(exc).__name__}: {exc}"
            print(f"[{account.client_slug}] FALHOU: {error_message}", file=sys.stderr)
            traceback.print_exc()

            # Nova transação curta só para registrar a falha — a
            # anterior foi abortada pelo rollback acima.
            try:
                cursor.execute("SELECT id FROM platforms WHERE slug = 'meta_ads'")
                platform_id = cursor.fetchone()["id"]
                cursor.execute(
                    "SELECT id FROM ad_accounts WHERE platform_id = %s AND external_account_id = %s",
                    (platform_id, account.external_account_id),
                )
                row = cursor.fetchone()
                if row:
                    cursor.execute(
                        """
                        INSERT INTO data_sync_runs
                            (ad_account_id, started_at, finished_at, status, error_message)
                        VALUES (%s, %s, %s, 'failed', %s)
                        """,
                        (row["id"], started_at, datetime.now(timezone.utc), error_message[:2000]),
                    )
                    conn.commit()
            except Exception:
                conn.rollback()

            return {"ok": False, "client_slug": account.client_slug, "error": error_message}


def sync_all(since: date, until: date, only: str | None = None) -> list[dict[str, Any]]:
    accounts = [a for a in ACCOUNTS if only is None or a.client_slug == only]

    if not accounts:
        raise ValueError(f"Nenhuma conta configurada com client_slug='{only}'")

    results = []
    for account in accounts:
        results.append(sync_account(account, since, until))

    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sincroniza dados do Meta Ads para o PostgreSQL.")
    parser.add_argument(
        "--days",
        type=int,
        default=DEFAULT_SYNC_DAYS,
        help=f"Janela de dias pra trás a sincronizar (padrão: {DEFAULT_SYNC_DAYS}).",
    )
    parser.add_argument(
        "--only",
        default=None,
        help="Sincronizar só o cliente com esse slug (padrão: todas as contas configuradas).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    until = date.today()
    since = until - timedelta(days=args.days)

    results = sync_all(since, until, only=args.only)

    failures = [r for r in results if not r["ok"]]
    if failures:
        print(f"\n{len(failures)} de {len(results)} conta(s) falharam.", file=sys.stderr)
        return 1

    print(f"\nTodas as {len(results)} conta(s) sincronizadas com sucesso.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
