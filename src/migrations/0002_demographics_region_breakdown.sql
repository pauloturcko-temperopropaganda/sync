-- ============================================================
-- 0002 — Breakdown de idade/gênero e região
-- ============================================================
-- Extensão do padrão já usado para device/publisher_platform
-- (ver 0001_core_schema.sql, comentário da tabela daily_metrics):
-- mais duas dimensões de breakdown como colunas diretas, não uma
-- tabela de dimensão genérica — o Meta continua combinando várias
-- dimensões numa linha só (aqui: age+gender numa chamada, region
-- noutra), então isso é só extensão das colunas existentes.
--
-- Confirmado empiricamente (2026-09-08, ver payload real da API)
-- que a Meta devolve `reach` e o array `actions` normalmente nos
-- dois breakdowns novos — diferente do breakdown combinado
-- publisher_platform+device, que não devolve reach. Por isso
-- daily_actions também ganha as mesmas 3 colunas aqui: dá pra saber
-- quantos leads vieram de cada faixa etária/gênero/região, o que o
-- breakdown de plataforma (Fase 1) não conseguia por falta dessas
-- colunas em daily_actions.
--
-- age_range/gender ficam sempre juntos (uma chamada `breakdowns=
-- age,gender`) e region sempre sozinho (`breakdowns=region`) — uma
-- linha nunca tem os dois grupos preenchidos ao mesmo tempo.
-- ============================================================

ALTER TABLE daily_metrics
    ADD COLUMN age_range VARCHAR(20),
    ADD COLUMN gender VARCHAR(20),
    ADD COLUMN region VARCHAR(100);

ALTER TABLE daily_metrics
    DROP CONSTRAINT daily_metrics_campaign_id_ad_group_id_ad_id_metric_date_dev_key;

ALTER TABLE daily_metrics
    ADD CONSTRAINT daily_metrics_unique_grain
    UNIQUE NULLS NOT DISTINCT (
        campaign_id, ad_group_id, ad_id, metric_date, device, publisher_platform,
        age_range, gender, region
    );

ALTER TABLE daily_actions
    ADD COLUMN age_range VARCHAR(20),
    ADD COLUMN gender VARCHAR(20),
    ADD COLUMN region VARCHAR(100);

ALTER TABLE daily_actions
    DROP CONSTRAINT daily_actions_campaign_id_ad_group_id_ad_id_metric_date_act_key;

ALTER TABLE daily_actions
    ADD CONSTRAINT daily_actions_unique_grain
    UNIQUE NULLS NOT DISTINCT (
        campaign_id, ad_group_id, ad_id, metric_date, action_type,
        age_range, gender, region
    );
