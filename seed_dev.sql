-- ============================================================
-- SYNC — Seed de desenvolvimento (PostgreSQL)
-- ============================================================
-- Dados fictícios para testar as ferramentas de src/ai_tools/*
-- contra o schema novo. NÃO é uma migration — não roda via
-- run_migrations.py, é executado manualmente:
--
--   psql -U sync_admin -d sync_db -f seed_dev.sql
--
-- Convenção: tudo prefixado com "seed-" / "SEED-" para nunca
-- ser confundido com dado real de cliente.
--
-- Inclui de propósito uma linha de daily_metrics e uma de
-- daily_actions em grão mais fino (device / ad_group) para
-- comprovar que os filtros de grão das ferramentas de IA as
-- ignoram corretamente e não contam duas vezes.
-- ============================================================

INSERT INTO organizations (slug, name) VALUES
    ('seed-agencia-teste', 'Agência Teste')
ON CONFLICT (slug) DO NOTHING;

INSERT INTO clients (organization_id, slug, name, industry) VALUES
    (
        (SELECT id FROM organizations WHERE slug = 'seed-agencia-teste'),
        'seed-cliente-teste',
        'Cliente Teste',
        'Saúde'
    )
ON CONFLICT (organization_id, slug) DO NOTHING;

INSERT INTO ad_accounts (client_id, platform_id, external_account_id, name, currency, timezone) VALUES
    (
        (SELECT id FROM clients WHERE slug = 'seed-cliente-teste'),
        (SELECT id FROM platforms WHERE slug = 'meta_ads'),
        'act_seed000001',
        'Cliente Teste - Meta Ads',
        'BRL',
        'America/Sao_Paulo'
    )
ON CONFLICT (platform_id, external_account_id) DO NOTHING;

INSERT INTO campaigns (ad_account_id, external_campaign_id, name, objective, status, start_date) VALUES
    (
        (SELECT id FROM ad_accounts WHERE external_account_id = 'act_seed000001'),
        'SEED-CAMP-LEADS',
        'Campanha Leads - Teste',
        'OUTCOME_LEADS',
        'ACTIVE',
        '2026-08-01'
    ),
    (
        (SELECT id FROM ad_accounts WHERE external_account_id = 'act_seed000001'),
        'SEED-CAMP-AWARENESS',
        'Campanha Awareness - Teste',
        'OUTCOME_AWARENESS',
        'PAUSED',
        '2026-08-01'
    )
ON CONFLICT (ad_account_id, external_campaign_id) DO NOTHING;

INSERT INTO ad_groups (campaign_id, external_ad_group_id, name, status, optimization_goal, daily_budget) VALUES
    (
        (SELECT id FROM campaigns WHERE external_campaign_id = 'SEED-CAMP-LEADS'),
        'SEED-ADSET-001',
        'Conjunto Leads - Teste',
        'ACTIVE',
        'LEAD_GENERATION',
        50.00
    )
ON CONFLICT (campaign_id, external_ad_group_id) DO NOTHING;

INSERT INTO ads (ad_group_id, external_ad_id, name, creative_type, status) VALUES
    (
        (SELECT id FROM ad_groups WHERE external_ad_group_id = 'SEED-ADSET-001'),
        'SEED-AD-001',
        'Criativo Leads - Teste',
        'VIDEO',
        'ACTIVE'
    )
ON CONFLICT (ad_group_id, external_ad_id) DO NOTHING;

-- Métricas diárias, grão campanha (ad_group_id/ad_id/device/publisher_platform nulos).
INSERT INTO daily_metrics (campaign_id, metric_date, impressions, clicks, spend, reach)
SELECT
    (SELECT id FROM campaigns WHERE external_campaign_id = 'SEED-CAMP-LEADS'),
    d.metric_date,
    5000 + (random() * 2000)::int,
    150 + (random() * 60)::int,
    ROUND((80 + random() * 40)::numeric, 2),
    3000 + (random() * 1000)::int
FROM generate_series('2026-08-01'::date, '2026-08-05'::date, interval '1 day') AS d(metric_date)
ON CONFLICT (campaign_id, ad_group_id, ad_id, metric_date, device, publisher_platform) DO NOTHING;

-- Linha em grão MAIS FINO (device preenchido) de propósito — as
-- ferramentas de IA devem ignorar isso no agregado de campanha.
INSERT INTO daily_metrics (campaign_id, metric_date, device, impressions, clicks, spend)
VALUES (
    (SELECT id FROM campaigns WHERE external_campaign_id = 'SEED-CAMP-LEADS'),
    '2026-08-01',
    'iphone',
    1200,
    40,
    18.50
)
ON CONFLICT (campaign_id, ad_group_id, ad_id, metric_date, device, publisher_platform) DO NOTHING;

-- Ações: mistura de action_type canônico e variantes redundantes,
-- igual ao que a exploração real do Meta mostrou.
INSERT INTO daily_actions (campaign_id, metric_date, action_type, count, value)
SELECT
    (SELECT id FROM campaigns WHERE external_campaign_id = 'SEED-CAMP-LEADS'),
    d.metric_date,
    v.action_type,
    v.count,
    v.value
FROM generate_series('2026-08-01'::date, '2026-08-05'::date, interval '1 day') AS d(metric_date)
CROSS JOIN (VALUES
    ('lead', 3::numeric, NULL::numeric),
    ('onsite_conversion.lead_grouped', 3::numeric, NULL::numeric),
    ('offsite_conversion.fb_pixel_lead', 2::numeric, NULL::numeric),
    ('link_click', 45::numeric, NULL::numeric),
    ('post_engagement', 120::numeric, NULL::numeric)
) AS v(action_type, count, value)
ON CONFLICT (campaign_id, ad_group_id, ad_id, metric_date, action_type) DO NOTHING;

-- Linha em grão de ad_group de propósito — deve ser ignorada no
-- agregado por cliente/campanha das ferramentas de IA.
INSERT INTO daily_actions (campaign_id, ad_group_id, metric_date, action_type, count)
VALUES (
    (SELECT id FROM campaigns WHERE external_campaign_id = 'SEED-CAMP-LEADS'),
    (SELECT id FROM ad_groups WHERE external_ad_group_id = 'SEED-ADSET-001'),
    '2026-08-01',
    'lead',
    999
)
ON CONFLICT (campaign_id, ad_group_id, ad_id, metric_date, action_type) DO NOTHING;

-- ============================================================
-- Dado adicional para testar get_client_performance (agregado
-- de TODAS as campanhas do cliente) e get_campaign_device_breakdown.
-- Valores fixos (não random()) de propósito, para dar pra conferir
-- a soma esperada na mão.
-- ============================================================

-- Métrica de campanha para a segunda campanha (Awareness), grão
-- campanha. Sem isso, get_client_performance só teria uma campanha
-- com dado e não testaria a soma entre campanhas de verdade.
INSERT INTO daily_metrics (campaign_id, metric_date, impressions, clicks, spend, reach)
VALUES (
    (SELECT id FROM campaigns WHERE external_campaign_id = 'SEED-CAMP-AWARENESS'),
    '2026-08-01', 2000, 30, 15.00, 1800
)
ON CONFLICT (campaign_id, ad_group_id, ad_id, metric_date, device, publisher_platform) DO NOTHING;

-- Breakdown por device + publisher_platform na campanha de Leads,
-- valores fixos: desktop/facebook e android_smartphone/instagram.
INSERT INTO daily_metrics (campaign_id, metric_date, device, publisher_platform, impressions, clicks, spend)
VALUES
    (
        (SELECT id FROM campaigns WHERE external_campaign_id = 'SEED-CAMP-LEADS'),
        '2026-08-02', 'desktop', 'facebook', 800, 20, 10.00
    ),
    (
        (SELECT id FROM campaigns WHERE external_campaign_id = 'SEED-CAMP-LEADS'),
        '2026-08-02', 'android_smartphone', 'instagram', 1500, 55, 22.00
    )
ON CONFLICT (campaign_id, ad_group_id, ad_id, metric_date, device, publisher_platform) DO NOTHING;
