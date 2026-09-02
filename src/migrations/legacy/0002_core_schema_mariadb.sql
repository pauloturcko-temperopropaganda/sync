-- ============================================================
-- SYNC — Core Schema v2
-- ============================================================
-- Esta migration inicia a nova arquitetura do banco.
--
-- IMPORTANTE:
-- Não depende do schema anterior para representar o domínio.
-- O schema antigo permanece como checkpoint histórico.
-- ============================================================
USE sync_db;

-- ============================================================
-- 0. CONTROLE DE MIGRATIONS
-- ============================================================
CREATE TABLE
    schema_migrations (
        id INT AUTO_INCREMENT PRIMARY KEY,
        filename VARCHAR(255) NOT NULL UNIQUE,
        applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ) ENGINE = InnoDB;

-- ============================================================
-- 1. ORGANIZATIONS
-- ============================================================
-- Representa a empresa/holding por trás de uma ou mais marcas.
--
-- Exemplo:
--
-- Organization: Empresa do Pepino
--     ├── Client: Pepino Premium
--     └── Client: Pepino Econômico
--
-- Na maioria dos casos:
--
-- Organization 1 ─── 1 Client
--
-- Mas também suporta:
--
-- Organization 1 ─── N Clients
-- ============================================================
CREATE TABLE
    organizations (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(200) NOT NULL,
        slug VARCHAR(200) NOT NULL UNIQUE,
        status ENUM ('active', 'inactive') NOT NULL DEFAULT 'active',
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE = InnoDB;

-- ============================================================
-- 2. CLIENTS
-- ============================================================
-- Representa a marca/unidade que a agência trata como cliente.
--
-- Um Organization pode possuir vários Clients.
--
-- Cada Client pode possuir várias contas de mídia.
-- ============================================================
CREATE TABLE
    clients (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        organization_id BIGINT NOT NULL,
        name VARCHAR(200) NOT NULL,
        slug VARCHAR(200) NOT NULL,
        industry VARCHAR(150),
        status ENUM ('active', 'inactive') NOT NULL DEFAULT 'active',
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        CONSTRAINT fk_clients_organization FOREIGN KEY (organization_id) REFERENCES organizations (id) ON DELETE RESTRICT,
        UNIQUE KEY uq_clients_organization_slug (organization_id, slug),
        INDEX idx_clients_organization (organization_id)
    ) ENGINE = InnoDB;

-- ============================================================
-- 3. PLATFORMS
-- ============================================================
-- Plataformas de mídia suportadas pelo Sync.
-- ============================================================
CREATE TABLE
    platforms (
        id SMALLINT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        slug VARCHAR(100) NOT NULL UNIQUE,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ) ENGINE = InnoDB;

INSERT INTO
    platforms (name, slug)
VALUES
    ('Google Ads', 'google_ads'),
    ('Meta Ads', 'meta_ads'),
    ('LinkedIn Ads', 'linkedin_ads'),
    ('TikTok Ads', 'tiktok_ads');

-- ============================================================
-- 4. AD ACCOUNTS
-- ============================================================
-- Conta de publicidade dentro de uma plataforma.
--
-- Exemplo:
--
-- Client
--    ├── Google Ads Account
--    ├── Meta Ads Account
--    └── TikTok Ads Account
--
-- Um Client pode possuir várias contas na mesma plataforma.
-- ============================================================
CREATE TABLE
    ad_accounts (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        client_id BIGINT NOT NULL,
        platform_id SMALLINT NOT NULL,
        external_account_id VARCHAR(150) NOT NULL,
        name VARCHAR(200),
        currency CHAR(3),
        timezone VARCHAR(100),
        status ENUM ('active', 'inactive') NOT NULL DEFAULT 'active',
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        CONSTRAINT fk_ad_accounts_client FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE RESTRICT,
        CONSTRAINT fk_ad_accounts_platform FOREIGN KEY (platform_id) REFERENCES platforms (id) ON DELETE RESTRICT,
        UNIQUE KEY uq_ad_account_platform_external (platform_id, external_account_id),
        INDEX idx_ad_accounts_client (client_id),
        INDEX idx_ad_accounts_platform (platform_id)
    ) ENGINE = InnoDB;

-- ============================================================
-- 5. CAMPAIGNS
-- ============================================================
-- Entidade de campanha normalizada.
--
-- A estrutura comum entre plataformas fica aqui.
-- Informações específicas de cada plataforma serão adicionadas
-- posteriormente em estruturas específicas.
-- ============================================================
CREATE TABLE
    campaigns (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        ad_account_id BIGINT NOT NULL,
        external_campaign_id VARCHAR(150) NOT NULL,
        name VARCHAR(300) NOT NULL,
        objective VARCHAR(150),
        campaign_type VARCHAR(150),
        status VARCHAR(100),
        start_date DATE,
        end_date DATE,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        CONSTRAINT fk_campaigns_ad_account FOREIGN KEY (ad_account_id) REFERENCES ad_accounts (id) ON DELETE RESTRICT,
        UNIQUE KEY uq_campaign_account_external (ad_account_id, external_campaign_id),
        INDEX idx_campaigns_account (ad_account_id),
        INDEX idx_campaigns_dates (start_date, end_date)
    ) ENGINE = InnoDB;

-- ============================================================
-- 6. AD GROUPS / AD SETS
-- ============================================================
-- Camada intermediária entre campanha e anúncio.
--
-- Google Ads → Ad Group
-- Meta Ads   → Ad Set
-- etc.
--
-- O nome interno será ad_groups para manter uma abstração
-- comum entre plataformas.
-- ============================================================
CREATE TABLE
    ad_groups (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        campaign_id BIGINT NOT NULL,
        external_ad_group_id VARCHAR(150) NOT NULL,
        name VARCHAR(300) NOT NULL,
        status VARCHAR(100),
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        CONSTRAINT fk_ad_groups_campaign FOREIGN KEY (campaign_id) REFERENCES campaigns (id) ON DELETE RESTRICT,
        UNIQUE KEY uq_ad_group_campaign_external (campaign_id, external_ad_group_id),
        INDEX idx_ad_groups_campaign (campaign_id)
    ) ENGINE = InnoDB;

-- ============================================================
-- 7. ADS
-- ============================================================
-- Anúncio individual.
-- ============================================================
CREATE TABLE
    ads (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        ad_group_id BIGINT NOT NULL,
        external_ad_id VARCHAR(150) NOT NULL,
        name VARCHAR(300),
        ad_type VARCHAR(150),
        status VARCHAR(100),
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        CONSTRAINT fk_ads_ad_group FOREIGN KEY (ad_group_id) REFERENCES ad_groups (id) ON DELETE RESTRICT,
        UNIQUE KEY uq_ad_ad_group_external (ad_group_id, external_ad_id),
        INDEX idx_ads_ad_group (ad_group_id)
    ) ENGINE = InnoDB;

-- ============================================================
-- 8. METRIC DIMENSIONS
-- ============================================================
-- Dimensões que podem ser utilizadas para segmentar métricas.
--
-- Exemplos:
-- MOBILE
-- DESKTOP
-- TABLET
-- etc.
--
-- Nem toda plataforma terá as mesmas dimensões.
-- ============================================================
CREATE TABLE
    metric_dimensions (
        id SMALLINT AUTO_INCREMENT PRIMARY KEY,
        dimension_type VARCHAR(100) NOT NULL,
        dimension_value VARCHAR(150) NOT NULL,
        UNIQUE KEY uq_metric_dimension (dimension_type, dimension_value)
    ) ENGINE = InnoDB;

-- ============================================================
-- 9. DAILY METRICS
-- ============================================================
-- Performance agregada de mídia.
--
-- Uma linha representa:
--
--   anúncio
--   + data
--   + dimensão (quando existir)
--
-- Exemplo:
--
-- 2026-01-26 | Ad X | MOBILE
-- 2026-01-26 | Ad X | DESKTOP
--
-- Se não houver segmentação, metric_dimension_id será NULL.
-- ============================================================
CREATE TABLE
    daily_metrics (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        ad_id BIGINT NOT NULL,
        metric_date DATE NOT NULL,
        metric_dimension_id SMALLINT NULL,
        impressions BIGINT NOT NULL DEFAULT 0,
        clicks BIGINT NOT NULL DEFAULT 0,
        spend DECIMAL(18, 6) NOT NULL DEFAULT 0,
        reach BIGINT,
        video_views BIGINT,
        platform_conversions DECIMAL(18, 6) NOT NULL DEFAULT 0,
        platform_conversion_value DECIMAL(18, 6) NOT NULL DEFAULT 0,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_daily_metrics_ad FOREIGN KEY (ad_id) REFERENCES ads (id) ON DELETE RESTRICT,
        CONSTRAINT fk_daily_metrics_dimension FOREIGN KEY (metric_dimension_id) REFERENCES metric_dimensions (id) ON DELETE RESTRICT,
        UNIQUE KEY uq_daily_metric (ad_id, metric_date, metric_dimension_id),
        INDEX idx_daily_metrics_date (metric_date),
        INDEX idx_daily_metrics_ad_date (ad_id, metric_date)
    ) ENGINE = InnoDB;

-- ============================================================
-- 10. DATA SYNC RUNS
-- ============================================================
-- Registra cada execução de coleta de dados das plataformas.
--
-- Isso permitirá futuramente saber:
--
-- "Quando o Sync buscou esses dados?"
-- "A coleta terminou?"
-- "Deu erro?"
-- ============================================================
CREATE TABLE
    data_sync_runs (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        ad_account_id BIGINT NOT NULL,
        started_at DATETIME NOT NULL,
        finished_at DATETIME NULL,
        status ENUM ('running', 'success', 'partial', 'failed') NOT NULL DEFAULT 'running',
        records_processed BIGINT NOT NULL DEFAULT 0,
        error_message TEXT NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_sync_runs_ad_account FOREIGN KEY (ad_account_id) REFERENCES ad_accounts (id) ON DELETE RESTRICT,
        INDEX idx_sync_runs_account (ad_account_id),
        INDEX idx_sync_runs_started (started_at)
    ) ENGINE = InnoDB;