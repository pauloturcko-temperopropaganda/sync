-- ============================================================
-- SYNC — Schema inicial do banco de dados (Sprint 3)
-- Banco: MariaDB
-- ============================================================

USE sync_db;

-- ============================================================
-- 1. CLIENTES
-- ============================================================
CREATE TABLE clients (
                         id INT AUTO_INCREMENT PRIMARY KEY,
                         name VARCHAR(150) NOT NULL,
                         slug VARCHAR(150) NOT NULL UNIQUE,       -- usado para bater com a pasta do Vault (ex: cliente-x)
                         industry VARCHAR(100),                    -- segmento de mercado do cliente
                         status ENUM('active','inactive') NOT NULL DEFAULT 'active',
                         created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                         updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ============================================================
-- 2. PLATAFORMAS (tabela de apoio/lookup)
-- ============================================================
CREATE TABLE platforms (
                           id INT AUTO_INCREMENT PRIMARY KEY,
                           name VARCHAR(50) NOT NULL,
                           slug VARCHAR(50) NOT NULL UNIQUE
) ENGINE=InnoDB;

INSERT INTO platforms (name, slug) VALUES
                                       ('Google Ads', 'google_ads'),
                                       ('Meta Ads', 'meta_ads'),
                                       ('LinkedIn Ads', 'linkedin_ads'),
                                       ('TikTok Ads', 'tiktok_ads');

-- ============================================================
-- 3. CONTAS DE ANÚNCIO
-- Cada cliente pode ter uma conta em cada plataforma
-- ============================================================
CREATE TABLE ad_accounts (
                             id INT AUTO_INCREMENT PRIMARY KEY,
                             client_id INT NOT NULL,
                             platform_id INT NOT NULL,
                             external_account_id VARCHAR(100) NOT NULL,  -- ID da conta na plataforma (ex: Google Ads Customer ID)
                             name VARCHAR(150),
                             currency CHAR(3) DEFAULT 'BRL',
                             timezone VARCHAR(50) DEFAULT 'America/Sao_Paulo',
                             status ENUM('active','inactive') NOT NULL DEFAULT 'active',
                             created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                             updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                             FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
                             FOREIGN KEY (platform_id) REFERENCES platforms(id),
                             UNIQUE KEY uq_account_platform (platform_id, external_account_id)
) ENGINE=InnoDB;

-- ============================================================
-- 4. CAMPANHAS
-- ============================================================
CREATE TABLE campaigns (
                           id INT AUTO_INCREMENT PRIMARY KEY,
                           ad_account_id INT NOT NULL,
                           external_campaign_id VARCHAR(100) NOT NULL,
                           name VARCHAR(200) NOT NULL,
                           objective VARCHAR(50),                        -- ex: awareness, traffic, conversions, leads
                           status ENUM('active','paused','ended','draft') NOT NULL DEFAULT 'active',
                           budget_type ENUM('daily','lifetime'),
                           budget_amount DECIMAL(12,2),
                           start_date DATE,
                           end_date DATE,
                           created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                           updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                           FOREIGN KEY (ad_account_id) REFERENCES ad_accounts(id) ON DELETE CASCADE,
                           UNIQUE KEY uq_campaign_account (ad_account_id, external_campaign_id)
) ENGINE=InnoDB;

-- ============================================================
-- 5. CONJUNTOS DE ANÚNCIOS (ad groups / ad sets)
-- ============================================================
CREATE TABLE ad_groups (
                           id INT AUTO_INCREMENT PRIMARY KEY,
                           campaign_id INT NOT NULL,
                           external_ad_group_id VARCHAR(100) NOT NULL,
                           name VARCHAR(200) NOT NULL,
                           status ENUM('active','paused','ended','draft') NOT NULL DEFAULT 'active',
                           targeting_summary TEXT,                       -- descrição livre do público-alvo configurado
                           created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                           updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                           FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE,
                           UNIQUE KEY uq_adgroup_campaign (campaign_id, external_ad_group_id)
) ENGINE=InnoDB;

-- ============================================================
-- 6. ANÚNCIOS
-- ============================================================
CREATE TABLE ads (
                     id INT AUTO_INCREMENT PRIMARY KEY,
                     ad_group_id INT NOT NULL,
                     external_ad_id VARCHAR(100) NOT NULL,
                     name VARCHAR(200),
                     format VARCHAR(50),                           -- ex: image, video, carousel, search, responsive
                     headline VARCHAR(255),
                     description TEXT,
                     creative_url VARCHAR(500),
                     status ENUM('active','paused','ended','draft') NOT NULL DEFAULT 'active',
                     created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                     updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                     FOREIGN KEY (ad_group_id) REFERENCES ad_groups(id) ON DELETE CASCADE,
                     UNIQUE KEY uq_ad_adgroup (ad_group_id, external_ad_id)
) ENGINE=InnoDB;

-- ============================================================
-- 7. MÉTRICAS DIÁRIAS
-- Uma linha por anúncio, por dia. É o nível mais granular
-- que as plataformas normalmente fornecem — dá para agregar
-- por campanha/semana/mês depois via query ou no Power BI.
-- ============================================================
CREATE TABLE daily_metrics (
                               id BIGINT AUTO_INCREMENT PRIMARY KEY,
                               ad_id INT NOT NULL,
                               metric_date DATE NOT NULL,
                               impressions INT NOT NULL DEFAULT 0,
                               clicks INT NOT NULL DEFAULT 0,
                               spend DECIMAL(12,2) NOT NULL DEFAULT 0,
                               reach INT,
                               video_views INT,
                               platform_conversions INT NOT NULL DEFAULT 0,       -- conversões reportadas PELA plataforma
                               platform_conversion_value DECIMAL(12,2) NOT NULL DEFAULT 0,
                               created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                               FOREIGN KEY (ad_id) REFERENCES ads(id) ON DELETE CASCADE,
                               UNIQUE KEY uq_metric_ad_date (ad_id, metric_date),
                               INDEX idx_metrics_date (metric_date)
) ENGINE=InnoDB;

-- Observação: CTR, CPC e CPM não são armazenados — são calculados
-- a partir de impressions/clicks/spend, tanto em query quanto no Power BI.
-- Isso evita inconsistência entre valor salvo e valor real.

-- ============================================================
-- 8. LANDING PAGES
-- ============================================================
CREATE TABLE landing_pages (
                               id INT AUTO_INCREMENT PRIMARY KEY,
                               client_id INT NOT NULL,
                               name VARCHAR(150),
                               url VARCHAR(500) NOT NULL,
                               created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                               FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- 9. LEADS
-- ============================================================
CREATE TABLE leads (
                       id BIGINT AUTO_INCREMENT PRIMARY KEY,
                       client_id INT NOT NULL,
                       landing_page_id INT,
                       campaign_id INT,           -- atribuição: de qual campanha esse lead veio
                       ad_id INT,                 -- atribuição: de qual anúncio esse lead veio
                       source VARCHAR(50),        -- ex: google_ads, meta_ads, organic, referral
                       name VARCHAR(150),
                       email VARCHAR(150),
                       phone VARCHAR(30),
                       status ENUM('new','contacted','qualified','converted','lost') NOT NULL DEFAULT 'new',
                       created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                       updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                       FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
                       FOREIGN KEY (landing_page_id) REFERENCES landing_pages(id) ON DELETE SET NULL,
                       FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE SET NULL,
                       FOREIGN KEY (ad_id) REFERENCES ads(id) ON DELETE SET NULL,
                       INDEX idx_leads_created (created_at)
) ENGINE=InnoDB;

-- ============================================================
-- 10. CONVERSÕES
-- Separado de platform_conversions porque nem sempre o que a
-- plataforma chama de "conversão" é o que a agência considera
-- conversão de verdade (ex: lead qualificado, venda fechada).
-- ============================================================
CREATE TABLE conversions (
                             id BIGINT AUTO_INCREMENT PRIMARY KEY,
                             client_id INT NOT NULL,
                             lead_id BIGINT,
                             campaign_id INT,
                             type VARCHAR(50) NOT NULL,     -- ex: purchase, signup, appointment, mql, sql
                             value DECIMAL(12,2) DEFAULT 0,
                             conversion_date DATE NOT NULL,
                             created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                             FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
                             FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE SET NULL,
                             FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE SET NULL,
                             INDEX idx_conversions_date (conversion_date)
) ENGINE=InnoDB;

-- ============================================================
-- 11. CONTROLE DE MIGRATIONS
-- Registra quais arquivos de migration já foram aplicados,
-- para o script Python (Sprint 4) saber o que falta rodar.
-- ============================================================
CREATE TABLE schema_migrations (
                                   id INT AUTO_INCREMENT PRIMARY KEY,
                                   filename VARCHAR(255) NOT NULL UNIQUE,
                                   applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;
