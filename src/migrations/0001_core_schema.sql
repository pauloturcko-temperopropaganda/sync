-- ============================================================
-- SYNC — Core Schema (PostgreSQL)
-- ============================================================
-- Primeira migration do banco em PostgreSQL. Substitui as
-- migrations antigas em MariaDB (preservadas em legacy/, nunca
-- executadas por este runner).
--
-- Desenhado a partir de exploração real das APIs do Meta Ads e
-- do Google Ads (ver docs/meta-ads-api-exploracao.md e
-- docs/archive/google-ads-api-exploracao/). Prioridade atual é
-- Meta Ads, mas a hierarquia (organizations -> clients ->
-- ad_accounts -> campaigns -> ad_groups -> ads) e a tabela
-- platforms são genéricas por plataforma, sem nada específico
-- de Meta nelas.
-- ============================================================

-- ============================================================
-- 0. CONTROLE DE MIGRATIONS
-- ============================================================
CREATE TABLE schema_migrations (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    filename VARCHAR(255) NOT NULL UNIQUE,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- Função utilitária: mantém updated_at em UPDATE.
-- Postgres não tem "ON UPDATE CURRENT_TIMESTAMP" como o MySQL/
-- MariaDB tinham — isso é o jeito idiomático de reproduzir o
-- mesmo comportamento.
-- ============================================================
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- 1. ORGANIZATIONS
-- ============================================================
-- Holding/grupo econômico dono de uma ou mais marcas.
-- Na maioria dos casos é 1:1 com clients, mas suporta grupos
-- com múltiplas marcas.
-- ============================================================
CREATE TABLE organizations (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    slug VARCHAR(200) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TRIGGER trg_organizations_updated_at
    BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- 2. CLIENTS
-- ============================================================
-- A marca/cliente da agência. slug é a chave de correlação com
-- a pasta correspondente no Vault (vault/Sync/clientes/<slug>).
-- ============================================================
CREATE TABLE clients (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL REFERENCES organizations(id),
    slug VARCHAR(200) NOT NULL,
    name VARCHAR(200) NOT NULL,
    industry VARCHAR(150),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (organization_id, slug)
);

CREATE INDEX idx_clients_organization ON clients (organization_id);

CREATE TRIGGER trg_clients_updated_at
    BEFORE UPDATE ON clients
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- 3. PLATFORMS
-- ============================================================
-- Lookup de plataformas de mídia suportadas. Meta Ads é o foco
-- atual; as demais existem para a integração futura não exigir
-- alteração de schema, só nova linha aqui.
-- ============================================================
CREATE TABLE platforms (
    id SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    slug VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL
);

INSERT INTO platforms (slug, name) VALUES
    ('meta_ads', 'Meta Ads'),
    ('google_ads', 'Google Ads'),
    ('linkedin_ads', 'LinkedIn Ads'),
    ('tiktok_ads', 'TikTok Ads');

-- ============================================================
-- 4. AD ACCOUNTS
-- ============================================================
CREATE TABLE ad_accounts (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    client_id BIGINT NOT NULL REFERENCES clients(id),
    platform_id SMALLINT NOT NULL REFERENCES platforms(id),
    external_account_id VARCHAR(150) NOT NULL,
    name VARCHAR(200),
    currency CHAR(3),
    timezone VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (platform_id, external_account_id)
);

CREATE INDEX idx_ad_accounts_client ON ad_accounts (client_id);

CREATE TRIGGER trg_ad_accounts_updated_at
    BEFORE UPDATE ON ad_accounts
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- 5. CAMPAIGNS
-- ============================================================
-- objective e status ficam como texto livre (não ENUM/lookup):
-- a exploração real mostrou o Meta usando tanto nomenclatura
-- nova (OUTCOME_LEADS) quanto antiga (LINK_CLICKS) na mesma
-- conta, e o Google tem seu próprio conjunto. Um enum rígido
-- quebraria a cada valor novo encontrado.
-- ============================================================
CREATE TABLE campaigns (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ad_account_id BIGINT NOT NULL REFERENCES ad_accounts(id),
    external_campaign_id VARCHAR(150) NOT NULL,
    name VARCHAR(300) NOT NULL,
    objective VARCHAR(150),
    status VARCHAR(50),
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (ad_account_id, external_campaign_id)
);

CREATE INDEX idx_campaigns_ad_account ON campaigns (ad_account_id);

CREATE TRIGGER trg_campaigns_updated_at
    BEFORE UPDATE ON campaigns
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- 6. AD GROUPS
-- ============================================================
-- Nome genérico cobrindo Ad Group (Google) / Ad Set (Meta).
-- daily_budget/lifetime_budget são mutuamente exclusivos na
-- prática (a API sempre retorna um deles como zero) — mantidos
-- como dois campos nuláveis em vez de um campo + tipo, para
-- bater 1:1 com o formato que as APIs realmente devolvem.
-- ============================================================
CREATE TABLE ad_groups (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    campaign_id BIGINT NOT NULL REFERENCES campaigns(id),
    external_ad_group_id VARCHAR(150) NOT NULL,
    name VARCHAR(300) NOT NULL,
    status VARCHAR(50),
    optimization_goal VARCHAR(100),
    daily_budget NUMERIC(14, 2),
    lifetime_budget NUMERIC(14, 2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (campaign_id, external_ad_group_id)
);

CREATE INDEX idx_ad_groups_campaign ON ad_groups (campaign_id);

CREATE TRIGGER trg_ad_groups_updated_at
    BEFORE UPDATE ON ad_groups
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- 7. ADS
-- ============================================================
CREATE TABLE ads (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ad_group_id BIGINT NOT NULL REFERENCES ad_groups(id),
    external_ad_id VARCHAR(150) NOT NULL,
    name VARCHAR(500),
    creative_type VARCHAR(100),
    status VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (ad_group_id, external_ad_id)
);

CREATE INDEX idx_ads_ad_group ON ads (ad_group_id);

CREATE TRIGGER trg_ads_updated_at
    BEFORE UPDATE ON ads
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- 8. DAILY METRICS (fato — números "limpos")
-- ============================================================
-- campaign_id é obrigatório; ad_group_id/ad_id são opcionais.
-- Isso corrige o erro do schema antigo (métrica amarrada a
-- ad_id, impossibilitando gravar relatório só de campanha).
-- Uma sincronização que só traz dado por campanha grava com
-- ad_group_id/ad_id nulos; se um dia buscarmos o nível de
-- anúncio individual, a mesma tabela recebe esses campos
-- preenchidos, sem precisar de tabela por granularidade.
--
-- device/publisher_platform ficam como colunas diretas (não
-- uma tabela de dimensão genérica): o Meta combina várias
-- dimensões numa linha só, o que ficaria estranho de
-- representar com uma dimensão só por linha. publisher_platform
-- é conceito exclusivo do Meta — fica NULL para outras
-- plataformas, o que é uma troca aceitável pela simplicidade.
--
-- UNIQUE ... NULLS NOT DISTINCT (recurso do Postgres 15+):
-- sem isso, duas linhas de campanha (ad_group_id/ad_id nulos)
-- no mesmo dia NÃO seriam pegas como duplicata pelo Postgres,
-- porque NULL nunca é igual a NULL numa UNIQUE constraint
-- normal. Esse recurso resolve isso, permitindo
-- INSERT ... ON CONFLICT DO UPDATE funcionar de verdade como
-- upsert idempotente em qualquer grão.
-- ============================================================
CREATE TABLE daily_metrics (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    campaign_id BIGINT NOT NULL REFERENCES campaigns(id),
    ad_group_id BIGINT REFERENCES ad_groups(id),
    ad_id BIGINT REFERENCES ads(id),
    metric_date DATE NOT NULL,
    device VARCHAR(50),
    publisher_platform VARCHAR(50),
    impressions BIGINT NOT NULL DEFAULT 0,
    clicks BIGINT NOT NULL DEFAULT 0,
    spend NUMERIC(14, 2) NOT NULL DEFAULT 0,
    reach BIGINT,
    frequency NUMERIC(10, 4),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE NULLS NOT DISTINCT (
        campaign_id, ad_group_id, ad_id, metric_date, device, publisher_platform
    )
);

CREATE INDEX idx_daily_metrics_campaign_date ON daily_metrics (campaign_id, metric_date);
CREATE INDEX idx_daily_metrics_date ON daily_metrics (metric_date);

-- ============================================================
-- 9. ACTION TYPE CATALOG
-- ============================================================
-- Achado central da exploração do Meta: o array `actions` do
-- /insights devolve o MESMO evento real sob vários action_type
-- diferentes (ex.: 9 variantes só para "lead"). Não resolvemos
-- isso na ingestão — gravamos tudo cru em daily_actions — e
-- usamos esta tabela para marcar qual action_type é o canônico
-- por categoria de negócio, para os relatórios filtrarem sem
-- contar duplicado.
--
-- IMPORTANTE para quem for escrever o pipeline de ingestão:
-- action_type em daily_actions tem FK para cá. Um action_type
-- nunca visto antes precisa ser inserido aqui primeiro (com
-- is_canonical = false, business_category = NULL) antes de
-- gravar a métrica — nunca falhar a ingestão por causa de um
-- action_type novo, só registrar como "não classificado ainda".
--
-- Seed abaixo com os action_type reais observados na exploração
-- (docs/meta-ads-api-exploracao.md, payloads/*_07_*.json).
-- Novidades da Meta no futuro entram do jeito acima.
-- ============================================================
CREATE TABLE action_type_catalog (
    action_type VARCHAR(150) PRIMARY KEY,
    platform_id SMALLINT NOT NULL REFERENCES platforms(id),
    business_category VARCHAR(50),
    is_canonical BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO action_type_catalog (action_type, platform_id, business_category, is_canonical)
SELECT v.action_type, p.id, v.business_category, v.is_canonical
FROM (VALUES
    -- lead
    ('lead', 'lead', true),
    ('onsite_conversion.lead_grouped', 'lead', false),
    ('onsite_conversion.lead', 'lead', false),
    ('offsite_conversion.fb_pixel_lead', 'lead', false),
    ('onsite_web_lead', 'lead', false),
    ('offsite_lead_add_20_s_calls', 'lead', false),
    ('offsite_complete_registration_add_meta_leads', 'lead', false),
    ('offsite_search_add_meta_leads', 'lead', false),
    ('offsite_content_view_add_meta_leads', 'lead', false),
    ('offsite_contact_website_add_meta_leads', 'lead', false),
    ('offsite_submit_application_add_meta_leads', 'lead', false),
    -- purchase
    ('purchase', 'purchase', true),
    ('omni_purchase', 'purchase', false),
    ('onsite_conversion.purchase', 'purchase', false),
    ('offsite_conversion.fb_pixel_purchase', 'purchase', false),
    ('onsite_web_purchase', 'purchase', false),
    ('onsite_web_app_purchase', 'purchase', false),
    ('onsite_app_purchase', 'purchase', false),
    ('web_in_store_purchase', 'purchase', false),
    ('web_app_in_store_purchase', 'purchase', false),
    ('offsite_purchase_add_20_s_calls', 'purchase', false),
    -- message (WhatsApp/Messenger)
    ('onsite_conversion.messaging_conversation_started_7d', 'message', true),
    ('onsite_conversion.total_messaging_connection', 'message', false),
    ('onsite_conversion.messaging_first_reply', 'message', false),
    ('onsite_conversion.messaging_conversation_replied_7d', 'message', false),
    ('onsite_conversion.messaging_welcome_message_view', 'message', false),
    ('onsite_conversion.messaging_block', 'message', false),
    ('onsite_conversion.messaging_user_depth_2_message_send', 'message', false),
    ('onsite_conversion.messaging_user_depth_3_message_send', 'message', false),
    ('onsite_conversion.messaging_user_depth_5_message_send', 'message', false),
    -- checkout
    ('initiate_checkout', 'checkout', true),
    ('onsite_web_initiate_checkout', 'checkout', false),
    ('omni_initiated_checkout', 'checkout', false),
    ('offsite_conversion.fb_pixel_initiate_checkout', 'checkout', false),
    ('offsite_initiate_checkout_add_20_s_calls', 'checkout', false),
    -- pageview
    ('landing_page_view', 'pageview', true),
    ('omni_landing_page_view', 'pageview', false),
    -- video
    ('video_view', 'video', true),
    -- engagement (rede social)
    ('link_click', 'engagement', true),
    ('post_engagement', 'engagement', false),
    ('page_engagement', 'engagement', false),
    ('post_reaction', 'engagement', false),
    ('like', 'engagement', false),
    ('comment', 'engagement', false),
    ('post', 'engagement', false),
    ('post_uncomment', 'engagement', false),
    ('post_unlike', 'engagement', false),
    ('post_interaction_gross', 'engagement', false),
    ('post_interaction_net', 'engagement', false),
    ('photo_view', 'engagement', false),
    ('onsite_conversion.post_save', 'engagement', false),
    ('onsite_conversion.post_unsave', 'engagement', false),
    ('onsite_conversion.post_net_save', 'engagement', false),
    ('onsite_conversion.post_net_like', 'engagement', false),
    ('onsite_conversion.post_net_comment', 'engagement', false),
    ('offsite_conversion.fb_pixel_custom', 'other', false),
    ('offsite_conversion.custom', 'other', false)
) AS v(action_type, business_category, is_canonical)
JOIN platforms p ON p.slug = 'meta_ads';

-- ============================================================
-- 10. DAILY ACTIONS (fato — array `actions` da Meta / conversion
-- actions do Google, granularidade própria por action_type)
-- ============================================================
CREATE TABLE daily_actions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    campaign_id BIGINT NOT NULL REFERENCES campaigns(id),
    ad_group_id BIGINT REFERENCES ad_groups(id),
    ad_id BIGINT REFERENCES ads(id),
    metric_date DATE NOT NULL,
    action_type VARCHAR(150) NOT NULL REFERENCES action_type_catalog (action_type),
    count NUMERIC(14, 2) NOT NULL DEFAULT 0,
    value NUMERIC(14, 2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE NULLS NOT DISTINCT (
        campaign_id, ad_group_id, ad_id, metric_date, action_type
    )
);

CREATE INDEX idx_daily_actions_campaign_date ON daily_actions (campaign_id, metric_date);
CREATE INDEX idx_daily_actions_type ON daily_actions (action_type);

-- ============================================================
-- 11. DATA SYNC RUNS
-- ============================================================
-- Observabilidade de cada execução de ingestão.
-- ============================================================
CREATE TABLE data_sync_runs (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ad_account_id BIGINT NOT NULL REFERENCES ad_accounts(id),
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'running',
    records_processed BIGINT NOT NULL DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_data_sync_runs_account ON data_sync_runs (ad_account_id);
CREATE INDEX idx_data_sync_runs_started ON data_sync_runs (started_at);
