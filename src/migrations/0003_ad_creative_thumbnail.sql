-- ============================================================
-- 0003 — Miniatura do criativo de cada anúncio
-- ============================================================
-- Guarda a thumbnail_url que a Meta devolve pra cada anúncio
-- (`/ads?fields=creative{thumbnail_url}`), usada na seção
-- "Principais Anúncios" do relatório. É uma URL assinada da CDN da
-- Meta com expiração embutida (parâmetro `oe`), não um asset
-- permanente — guardamos como veio, sem baixar/cachear a imagem em
-- si, porque relatórios normalmente cobrem período recente logo
-- depois de um sync. Se um relatório muito antigo, gerado bem depois
-- do último sync daquele anúncio, mostrar a miniatura quebrada, é
-- essa a causa.
-- ============================================================

ALTER TABLE ads
    ADD COLUMN creative_thumbnail_url TEXT;
