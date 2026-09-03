-- ============================================================
-- 0004 — Cadastros (leads) por plataforma
-- ============================================================
-- A seção "Resultado por Plataforma" do relatório (Fase 1) nunca
-- conseguiu mostrar leads por plataforma: o breakdown que o sync já
-- fazia (publisher_platform + device juntos, ver
-- sync_device_breakdown) não devolve `reach` nem `actions" utilizável
-- pra essa combinação — confirmado empiricamente na Fase 1.
--
-- Confirmado agora (2026-09-08) que um breakdown só de
-- publisher_platform (sem combinar com device) DEVOLVE reach e
-- actions normalmente — mesma descoberta que já tinha valido pra
-- age+gender e region na Fase 2. Por isso: nova coluna aqui (mesma
-- ideia da migration 0002) + um novo INSERT dedicado em
-- daily_metrics com device NULL (linha "só plataforma", separada das
-- linhas já existentes que combinam device+plataforma — não colide
-- porque device faz parte da chave única).
-- ============================================================

ALTER TABLE daily_actions
    ADD COLUMN publisher_platform VARCHAR(50);

ALTER TABLE daily_actions
    DROP CONSTRAINT daily_actions_unique_grain;

ALTER TABLE daily_actions
    ADD CONSTRAINT daily_actions_unique_grain
    UNIQUE NULLS NOT DISTINCT (
        campaign_id, ad_group_id, ad_id, metric_date, action_type,
        age_range, gender, region, publisher_platform
    );
