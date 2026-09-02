-- ============================================================
-- SYNC — Seed de dados de teste
-- Objetivo: popular o banco com dados fictícios para testes
-- de consultas, Python, IA e Power BI.
--
-- Pressuposto:
--   1. O schema.sql já foi executado.
--   2. A tabela platforms já contém os 4 registros definidos
--      no schema.sql.
--   3. Este seed usa IDs a partir de 1001 para preservar dados
--      que já existam nas tabelas.
--   4. INSERT IGNORE permite executar o seed novamente sem
--      interromper a migration por duplicidade de PK.
--
-- Observação:
--   schema_migrations não é populada aqui, pois essa tabela deve
--   ser controlada pelo mecanismo de migrations do projeto.
-- ============================================================

USE sync_db;

START TRANSACTION;

-- ============================================================
-- 1. CLIENTES
-- ============================================================

INSERT IGNORE INTO clients (id, name, slug, industry, status) VALUES
(1001, 'Alpha Imóveis', 'seed-alpha-imoveis',       'Imobiliária',              'active'),
(1002, 'Bella Odonto', 'seed-bella-odonto',        'Odontologia',              'active'),
(1003, 'Casa Norte Móveis', 'seed-casa-norte-moveis',   'Móveis e Decoração',       'active'),
(1004, 'FitLife Academia', 'seed-fitlife-academia',    'Academia e Fitness',       'active'),
(1005, 'TechParts Brasil', 'seed-techparts-brasil',    'Tecnologia e E-commerce',  'active');

-- ============================================================
-- 2. CONTAS DE ANÚNCIO
-- Cada cliente terá Meta Ads e Google Ads para permitir testes
-- de comparação entre plataformas.
-- IDs das plataformas permanecem os do schema.sql (1 = Google Ads, 2 = Meta Ads).
-- Os IDs deste seed começam em 1001 para não colidir com dados existentes.
-- ============================================================

INSERT IGNORE INTO ad_accounts
    (id, client_id, platform_id, external_account_id, name, currency, timezone, status)
VALUES
(1001,  1001, 1, 'SEED-G-100001', 'Alpha Imóveis - Google Ads',      'BRL', 'America/Sao_Paulo', 'active'),
(1002,  1001, 2, 'SEED-M-100001', 'Alpha Imóveis - Meta Ads',        'BRL', 'America/Sao_Paulo', 'active'),

(1003,  1002, 1, 'SEED-G-100002', 'Bella Odonto - Google Ads',       'BRL', 'America/Sao_Paulo', 'active'),
(1004,  1002, 2, 'SEED-M-100002', 'Bella Odonto - Meta Ads',         'BRL', 'America/Sao_Paulo', 'active'),

(1005,  1003, 1, 'SEED-G-100003', 'Casa Norte - Google Ads',         'BRL', 'America/Sao_Paulo', 'active'),
(1006,  1003, 2, 'SEED-M-100003', 'Casa Norte - Meta Ads',           'BRL', 'America/Sao_Paulo', 'active'),

(1007,  1004, 1, 'SEED-G-100004', 'FitLife - Google Ads',             'BRL', 'America/Sao_Paulo', 'active'),
(1008,  1004, 2, 'SEED-M-100004', 'FitLife - Meta Ads',               'BRL', 'America/Sao_Paulo', 'active'),

(1009,  1005, 1, 'SEED-G-100005', 'TechParts - Google Ads',            'BRL', 'America/Sao_Paulo', 'active'),
(1010,  1005, 2, 'SEED-M-100005', 'TechParts - Meta Ads',              'BRL', 'America/Sao_Paulo', 'active');

-- ============================================================
-- 3. CAMPANHAS
-- 3 campanhas por cliente/plataforma = 30 campanhas.
-- ============================================================

INSERT IGNORE INTO campaigns
    (id, ad_account_id, external_campaign_id, name, objective, status,
     budget_type, budget_amount, start_date, end_date)
VALUES
-- Alpha
(1001,  1001, 'SEED-GC-A01', 'Pesquisa - Imóveis',             'leads',       'active',  'daily',    120.00, '2026-07-01', NULL),
(1002,  1001, 'SEED-GC-A02', 'Marca - Alpha Imóveis',          'traffic',     'active',  'daily',     60.00, '2026-07-01', NULL),
(1003,  1001, 'SEED-GC-A03', 'Apartamentos - Centro',           'conversions', 'paused',  'daily',     90.00, '2026-06-15', '2026-07-31'),
(1004,  1002, 'SEED-MC-A01', 'Captação de Leads',              'leads',       'active',  'daily',    100.00, '2026-07-01', NULL),
(1005,  1002, 'SEED-MC-A02', 'Remarketing Imóveis',            'conversions', 'active',  'daily',     80.00, '2026-07-05', NULL),
(1006,  1002, 'SEED-MC-A03', 'Lançamento Residencial',         'awareness',   'ended',   'lifetime', 2500.00, '2026-06-01', '2026-06-30'),

-- Bella Odonto
(1007,  1003, 'SEED-GC-B01', 'Implantes Dentários',             'leads',       'active',  'daily',    140.00, '2026-07-01', NULL),
(1008,  1003, 'SEED-GC-B02', 'Clínica - Marca',                'traffic',     'active',  'daily',     50.00, '2026-07-01', NULL),
(1009,  1003, 'SEED-GC-B03', 'Ortodontia',                     'conversions', 'paused',  'daily',     90.00, '2026-06-10', '2026-07-20'),
(1010,  1004, 'SEED-MC-B01', 'Implantes - Leads',               'leads',       'active',  'daily',    110.00, '2026-07-01', NULL),
(1011,  1004, 'SEED-MC-B02', 'Aparelho Invisível',              'conversions', 'active',  'daily',     95.00, '2026-07-03', NULL),
(1012,  1004, 'SEED-MC-B03', 'Conteúdo e Marca',                'awareness',   'active',  'daily',     45.00, '2026-07-10', NULL),

-- Casa Norte
(1013,  1005, 'SEED-GC-C01', 'Móveis Planejados',              'leads',       'active',  'daily',    130.00, '2026-07-01', NULL),
(1014,  1005, 'SEED-GC-C02', 'Sala de Estar',                  'conversions', 'active',  'daily',    100.00, '2026-07-05', NULL),
(1015,  1005, 'SEED-GC-C03', 'Pesquisa de Marca',              'traffic',     'active',  'daily',     40.00, '2026-07-01', NULL),
(1016,  1006, 'SEED-MC-C01', 'Móveis Planejados - Leads',      'leads',       'active',  'daily',    120.00, '2026-07-01', NULL),
(1017,  1006, 'SEED-MC-C02', 'Remarketing - Catálogo',         'conversions', 'active',  'daily',     90.00, '2026-07-08', NULL),
(1018,  1006, 'SEED-MC-C03', 'Decoração - Inspiração',         'awareness',   'paused',  'daily',     70.00, '2026-06-15', '2026-07-25'),

-- FitLife
(1019,  1007, 'SEED-GC-D01', 'Academia - Matrículas',          'leads',       'active',  'daily',    100.00, '2026-07-01', NULL),
(1020,  1007, 'SEED-GC-D02', 'Personal Trainer',               'conversions', 'active',  'daily',     80.00, '2026-07-01', NULL),
(1021,  1007, 'SEED-GC-D03', 'Marca - FitLife',                'traffic',     'active',  'daily',     35.00, '2026-07-01', NULL),
(1022,  1008, 'SEED-MC-D01', 'Matrículas - Leads',             'leads',       'active',  'daily',     90.00, '2026-07-01', NULL),
(1023,  1008, 'SEED-MC-D02', 'Remarketing - Matrículas',       'conversions', 'active',  'daily',     75.00, '2026-07-05', NULL),
(1024,  1008, 'SEED-MC-D03', 'Desafio 30 Dias',                'awareness',   'ended',   'lifetime', 1800.00, '2026-06-01', '2026-06-30'),

-- TechParts
(1025,  1009, 'SEED-GC-E01', 'Componentes para PC',             'conversions', 'active',  'daily',    180.00, '2026-07-01', NULL),
(1026,  1009, 'SEED-GC-E02', 'Notebook Gamer',                 'conversions', 'active',  'daily',    220.00, '2026-07-01', NULL),
(1027,  1009, 'SEED-GC-E03', 'Marca - TechParts',              'traffic',     'active',  'daily',     50.00, '2026-07-01', NULL),
(1028,  1010, 'SEED-MC-E01', 'Componentes - Conversões',      'conversions', 'active',  'daily',    160.00, '2026-07-01', NULL),
(1029,  1010, 'SEED-MC-E02', 'Remarketing - Produtos',        'conversions', 'active',  'daily',    130.00, '2026-07-05', NULL),
(1030,  1010, 'SEED-MC-E03', 'Ofertas Semanais',              'traffic',     'active',  'daily',     70.00, '2026-07-10', NULL);

-- ============================================================
-- 4. CONJUNTOS / AD SETS
-- 2 por campanha = 60 registros.
-- ============================================================

INSERT IGNORE INTO ad_groups
    (id, campaign_id, external_ad_group_id, name, status, targeting_summary)
VALUES
-- Campaign 1-6
(1001,  1001, 'SEED-AG-001-A', 'Alta intenção',             'active', 'Usuários pesquisando imóveis para compra na região'),
(1002,  1001, 'SEED-AG-001-B', 'Compradores locais',         'active', 'Público local interessado em compra de imóveis'),
(1003,  1002, 'SEED-AG-002-A', 'Marca ampla',                'active', 'Público amplo da região'),
(1004,  1002, 'SEED-AG-002-B', 'Marca qualificada',          'active', 'Usuários que já visitaram o site'),
(1005,  1003, 'SEED-AG-003-A', 'Centro - apartamentos',      'ended',  'Pessoas interessadas em apartamentos no centro'),
(1006,  1003, 'SEED-AG-003-B', 'Centro - remarketing',       'ended',  'Visitantes recentes de páginas de apartamentos'),
(1007,  1004, 'SEED-AG-004-A', 'Lead imobiliário',            'active', 'Público 30-55 anos interessado em imóveis'),
(1008,  1004, 'SEED-AG-004-B', 'Lookalike leads',             'active', 'Público semelhante aos leads anteriores'),
(1009,  1005, 'SEED-AG-005-A', 'Visitantes 30 dias',           'active', 'Visitantes do site nos últimos 30 dias'),
(1010,  1005, 'SEED-AG-005-B', 'Engajados Instagram',          'active', 'Pessoas que interagiram com o perfil'),
(1011,  1006, 'SEED-AG-006-A', 'Lançamento região',            'ended',  'Público local interessado em novos empreendimentos'),
(1012,  1006, 'SEED-AG-006-B', 'Remarketing lançamento',       'ended',  'Visitantes das páginas do empreendimento'),

-- Campaign 7-12
(1013,  1007, 'SEED-AG-007-A', 'Implantes - intenção',         'active', 'Pessoas pesquisando implantes dentários'),
(1014,  1007, 'SEED-AG-007-B', 'Implantes - local',            'active', 'Público local interessado em odontologia'),
(1015,  1008, 'SEED-AG-008-A', 'Marca ampla',                  'active', 'Público local amplo'),
(1016,  1008, 'SEED-AG-008-B', 'Visitantes do site',            'active', 'Usuários que visitaram o site'),
(1017,  1009, 'SEED-AG-009-A', 'Ortodontia',                   'ended',  'Adultos interessados em ortodontia'),
(1018,  1009, 'SEED-AG-009-B', 'Remarketing ortodontia',       'ended',  'Visitantes de páginas de ortodontia'),
(1019,  1010, 'SEED-AG-010-A', 'Implantes - leads',           'active', 'Adultos 30-60 anos na região'),
(1020,  1010, 'SEED-AG-010-B', 'Lookalike pacientes',        'active', 'Público semelhante a pacientes existentes'),
(1021,  1011, 'SEED-AG-011-A', 'Aparelho invisível',          'active', 'Adultos interessados em estética dental'),
(1022,  1011, 'SEED-AG-011-B', 'Remarketing aparelho',        'active', 'Visitantes da página do produto'),
(1023,  1012, 'SEED-AG-012-A', 'Conteúdo saúde',               'active', 'Público interessado em saúde bucal'),
(1024,  1012, 'SEED-AG-012-B', 'Engajamento social',           'active', 'Usuários que interagiram com conteúdos'),

-- Campaign 13-18
(1025,  1013, 'SEED-AG-013-A', 'Planejados - intenção',       'active', 'Pessoas buscando móveis planejados'),
(1026,  1013, 'SEED-AG-013-B', 'Planejados - região',         'active', 'Público local interessado em móveis'),
(1027,  1014, 'SEED-AG-014-A', 'Sala de estar',                'active', 'Interesses em decoração e sala de estar'),
(1028,  1014, 'SEED-AG-014-B', 'Remarketing produtos',        'active', 'Visitantes de produtos da loja'),
(1029,  1015, 'SEED-AG-015-A', 'Marca ampla',                  'active', 'Público local amplo'),
(1030,  1015, 'SEED-AG-015-B', 'Visitantes do site',            'active', 'Usuários que visitaram o site'),
(1031,  1016, 'SEED-AG-016-A', 'Planejados - leads',           'active', 'Público 25-55 anos interessado em reforma'),
(1032,  1016, 'SEED-AG-016-B', 'Lookalike compradores',        'active', 'Público semelhante a compradores'),
(1033,  1017, 'SEED-AG-017-A', 'Catálogo',                     'active', 'Visitantes e interessados nos produtos'),
(1034,  1017, 'SEED-AG-017-B', 'Carrinho abandonado',          'active', 'Usuários que adicionaram produtos ao carrinho'),
(1035,  1018, 'SEED-AG-018-A', 'Inspiração decoração',         'ended',  'Público interessado em decoração'),
(1036,  1018, 'SEED-AG-018-B', 'Engajamento decoração',        'ended',  'Usuários que interagiram com conteúdos'),

-- Campaign 19-24
(1037,  1019, 'SEED-AG-019-A', 'Matrículas local',             'active', 'Pessoas próximas à academia interessadas em fitness'),
(1038,  1019, 'SEED-AG-019-B', 'Matrículas interesse',         'active', 'Interesses em academia e musculação'),
(1039,  1020, 'SEED-AG-020-A', 'Personal trainer',             'active', 'Público interessado em treinamento personalizado'),
(1040,  1020, 'SEED-AG-020-B', 'Alta renda fitness',           'active', 'Público com maior poder aquisitivo e interesse em fitness'),
(1041,  1021, 'SEED-AG-021-A', 'Marca ampla',                  'active', 'Público local amplo'),
(1042,  1021, 'SEED-AG-021-B', 'Visitantes do site',            'active', 'Usuários que visitaram o site'),
(1043,  1022, 'SEED-AG-022-A', 'Matrículas - leads',            'active', 'Adultos 20-50 anos interessados em academia'),
(1044,  1022, 'SEED-AG-022-B', 'Lookalike alunos',              'active', 'Público semelhante a alunos atuais'),
(1045,  1023, 'SEED-AG-023-A', 'Remarketing matrícula',         'active', 'Visitantes da página de matrícula'),
(1046,  1023, 'SEED-AG-023-B', 'Engajamento social',            'active', 'Pessoas que interagiram com o perfil'),
(1047,  1024, 'SEED-AG-024-A', 'Desafio 30 dias',               'ended',  'Público interessado em emagrecimento e fitness'),
(1048,  1024, 'SEED-AG-024-B', 'Remarketing desafio',           'ended',  'Visitantes e engajados no período'),

-- Campaign 25-30
(1049,  1025, 'SEED-AG-025-A', 'Componentes - intenção',       'active', 'Pessoas buscando componentes para PC'),
(1050,  1025, 'SEED-AG-025-B', 'Componentes - categoria',     'active', 'Interessados em hardware e informática'),
(1051,  1026, 'SEED-AG-026-A', 'Notebook gamer',              'active', 'Usuários interessados em notebooks gamer'),
(1052,  1026, 'SEED-AG-026-B', 'Remarketing notebook',        'active', 'Visitantes de páginas de notebooks'),
(1053,  1027, 'SEED-AG-027-A', 'Marca ampla',                 'active', 'Público interessado em tecnologia'),
(1054,  1027, 'SEED-AG-027-B', 'Visitantes do site',           'active', 'Usuários que visitaram a loja'),
(1055,  1028, 'SEED-AG-028-A', 'Componentes - conversão',     'active', 'Público com intenção de compra'),
(1056,  1028, 'SEED-AG-028-B', 'Lookalike compradores',        'active', 'Público semelhante aos compradores'),
(1057,  1029, 'SEED-AG-029-A', 'Remarketing produtos',         'active', 'Visitantes e carrinhos abandonados'),
(1058,  1029, 'SEED-AG-029-B', 'Clientes recorrentes',          'active', 'Clientes anteriores e públicos semelhantes'),
(1059,  1030, 'SEED-AG-030-A', 'Ofertas semanais',             'active', 'Público interessado em promoções de tecnologia'),
(1060,  1030, 'SEED-AG-030-B', 'Engajamento social',            'active', 'Usuários que interagiram com os conteúdos');

-- ============================================================
-- 5. ANÚNCIOS
-- 2 por conjunto = 120 registros.
-- ============================================================

INSERT IGNORE INTO ads
    (id, ad_group_id, external_ad_id, name, format, headline, description, creative_url, status)
VALUES
(1001,1001,'SEED-AD-001','Imóvel destaque - A','image','Encontre seu novo imóvel','Imóveis selecionados para você.','https://example.com/ads/ad-001.jpg','active'),
(1002,1001,'SEED-AD-002','Imóvel destaque - B','image','Apartamentos na sua região','Veja oportunidades disponíveis.','https://example.com/ads/ad-002.jpg','active'),
(1003,1002,'SEED-AD-003','Compra local - A','responsive','Compre seu imóvel','Atendimento especializado para compradores.','https://example.com/ads/ad-003.jpg','active'),
(1004,1002,'SEED-AD-004','Compra local - B','responsive','Encontre seu próximo lar','Fale com um consultor.','https://example.com/ads/ad-004.jpg','active'),
(1005,1003,'SEED-AD-005','Marca - A','responsive','Alpha Imóveis','Conheça a Alpha Imóveis.','https://example.com/ads/ad-005.jpg','active'),
(1006,1003,'SEED-AD-006','Marca - B','responsive','Imóveis com confiança','Experiência para ajudar você.','https://example.com/ads/ad-006.jpg','active'),
(1007,1004,'SEED-AD-007','Marca qualificada - A','responsive','Veja nossos imóveis','Opções para diferentes perfis.','https://example.com/ads/ad-007.jpg','active'),
(1008,1004,'SEED-AD-008','Marca qualificada - B','responsive','Fale com a Alpha','Converse com nossa equipe.','https://example.com/ads/ad-008.jpg','active'),
(1009,1005,'SEED-AD-009','Centro - A','image','Apartamentos no Centro','Confira os imóveis disponíveis.','https://example.com/ads/ad-009.jpg','ended'),
(1010,1005,'SEED-AD-010','Centro - B','image','More perto de tudo','Conheça as opções no centro.','https://example.com/ads/ad-010.jpg','ended'),
(1011,1006,'SEED-AD-011','Remarketing centro - A','carousel','Ainda procurando imóvel?','Veja novamente as opções.','https://example.com/ads/ad-011.jpg','ended'),
(1012,1006,'SEED-AD-012','Remarketing centro - B','carousel','Seu próximo imóvel pode estar aqui','Retome sua busca.','https://example.com/ads/ad-012.jpg','ended'),
(1013,1007,'SEED-AD-013','Captação - A','image','Encontre seu imóvel ideal','Receba atendimento personalizado.','https://example.com/ads/ad-013.jpg','active'),
(1014,1007,'SEED-AD-014','Captação - B','image','Fale com um especialista','Nossa equipe pode ajudar.','https://example.com/ads/ad-014.jpg','active'),
(1015,1008,'SEED-AD-015','Lookalike - A','image','O imóvel certo para você','Conheça nossas oportunidades.','https://example.com/ads/ad-015.jpg','active'),
(1016,1008,'SEED-AD-016','Lookalike - B','video','Conheça nossas opções','Veja os destaques da semana.','https://example.com/ads/ad-016.jpg','active'),
(1017,1009,'SEED-AD-017','Remarketing - A','carousel','Você ainda pode encontrar seu imóvel','Confira novamente os anúncios.','https://example.com/ads/ad-017.jpg','active'),
(1018,1009,'SEED-AD-018','Remarketing - B','carousel','Continue sua busca','Veja imóveis semelhantes.','https://example.com/ads/ad-018.jpg','active'),
(1019,1010,'SEED-AD-019','Instagram - A','video','Novos imóveis toda semana','Acompanhe as oportunidades.','https://example.com/ads/ad-019.jpg','active'),
(1020,1010,'SEED-AD-020','Instagram - B','image','Descubra novas opções','Confira nossos destaques.','https://example.com/ads/ad-020.jpg','active'),
(1021,1011,'SEED-AD-021','Lançamento - A','video','Conheça o novo empreendimento','Agende uma visita.','https://example.com/ads/ad-021.jpg','ended'),
(1022,1011,'SEED-AD-022','Lançamento - B','carousel','Seu novo endereço','Conheça detalhes do lançamento.','https://example.com/ads/ad-022.jpg','ended'),
(1023,1012,'SEED-AD-023','Remarketing lançamento - A','carousel','Ainda pensando neste imóvel?','Fale com nosso time.','https://example.com/ads/ad-023.jpg','ended'),
(1024,1012,'SEED-AD-024','Remarketing lançamento - B','image','Agende sua visita','Últimas oportunidades.','https://example.com/ads/ad-024.jpg','ended'),

(1025,1013,'SEED-AD-025','Implantes - A','search','Implante dentário','Avaliação e atendimento especializado.','https://example.com/ads/ad-025.jpg','active'),
(1026,1013,'SEED-AD-026','Implantes - B','search','Implantes dentários','Agende sua avaliação.','https://example.com/ads/ad-026.jpg','active'),
(1027,1014,'SEED-AD-027','Implantes local - A','image','Seu sorriso merece cuidado','Conheça a Bella Odonto.','https://example.com/ads/ad-027.jpg','active'),
(1028,1014,'SEED-AD-028','Implantes local - B','image','Avaliação odontológica','Atendimento especializado.','https://example.com/ads/ad-028.jpg','active'),
(1029,1015,'SEED-AD-029','Marca - A','responsive','Bella Odonto','Conheça nossa clínica.','https://example.com/ads/ad-029.jpg','active'),
(1030,1015,'SEED-AD-030','Marca - B','responsive','Cuidando do seu sorriso','Conte com nossa equipe.','https://example.com/ads/ad-030.jpg','active'),
(1031,1016,'SEED-AD-031','Visitantes - A','image','Volte a conhecer a Bella','Veja nossos tratamentos.','https://example.com/ads/ad-031.jpg','active'),
(1032,1016,'SEED-AD-032','Visitantes - B','video','Seu sorriso em boas mãos','Agende sua avaliação.','https://example.com/ads/ad-032.jpg','active'),
(1033,1017,'SEED-AD-033','Ortodontia - A','search','Aparelho ortodôntico','Opções para seu tratamento.','https://example.com/ads/ad-033.jpg','ended'),
(1034,1017,'SEED-AD-034','Ortodontia - B','search','Ortodontia especializada','Fale com nossa equipe.','https://example.com/ads/ad-034.jpg','ended'),
(1035,1018,'SEED-AD-035','Remarketing ortodontia - A','image','Ainda pensando no tratamento?','Retome seu atendimento.','https://example.com/ads/ad-035.jpg','ended'),
(1036,1018,'SEED-AD-036','Remarketing ortodontia - B','carousel','Conheça nossas opções','Veja as possibilidades.','https://example.com/ads/ad-036.jpg','ended'),
(1037,1019,'SEED-AD-037','Leads implantes - A','image','Agende sua avaliação','Fale com um especialista.','https://example.com/ads/ad-037.jpg','active'),
(1038,1019,'SEED-AD-038','Leads implantes - B','video','Transforme seu sorriso','Conheça nosso atendimento.','https://example.com/ads/ad-038.jpg','active'),
(1039,1020,'SEED-AD-039','Lookalike pacientes - A','image','Tratamentos para você','Conheça nossas soluções.','https://example.com/ads/ad-039.jpg','active'),
(1040,1020,'SEED-AD-040','Lookalike pacientes - B','image','Cuide do seu sorriso','Agende uma consulta.','https://example.com/ads/ad-040.jpg','active'),
(1041,1021,'SEED-AD-041','Aparelho invisível - A','video','Sorriso alinhado','Conheça o aparelho invisível.','https://example.com/ads/ad-041.jpg','active'),
(1042,1021,'SEED-AD-042','Aparelho invisível - B','image','Discrição e tecnologia','Saiba mais sobre o tratamento.','https://example.com/ads/ad-042.jpg','active'),
(1043,1022,'SEED-AD-043','Remarketing aparelho - A','image','Seu tratamento continua aqui','Tire suas dúvidas.','https://example.com/ads/ad-043.jpg','active'),
(1044,1022,'SEED-AD-044','Remarketing aparelho - B','carousel','Dê o próximo passo','Agende uma avaliação.','https://example.com/ads/ad-044.jpg','active'),
(1045,1023,'SEED-AD-045','Conteúdo saúde - A','video','Cuidados com a saúde bucal','Informações para seu sorriso.','https://example.com/ads/ad-045.jpg','active'),
(1046,1023,'SEED-AD-046','Conteúdo saúde - B','image','Prevenção começa agora','Veja nossas dicas.','https://example.com/ads/ad-046.jpg','active'),
(1047,1024,'SEED-AD-047','Engajamento - A','video','Saúde bucal sem complicação','Acompanhe nossos conteúdos.','https://example.com/ads/ad-047.jpg','active'),
(1048,1024,'SEED-AD-048','Engajamento - B','image','Conheça a Bella Odonto','Conteúdo e informação.','https://example.com/ads/ad-048.jpg','active'),

(1049,1025,'SEED-AD-049','Planejados - A','image','Móveis planejados sob medida','Projete seu ambiente.','https://example.com/ads/ad-049.jpg','active'),
(1050,1025,'SEED-AD-050','Planejados - B','image','Seu ambiente do seu jeito','Solicite um orçamento.','https://example.com/ads/ad-050.jpg','active'),
(1051,1026,'SEED-AD-051','Planejados região - A','video','Transforme sua casa','Conheça nossos projetos.','https://example.com/ads/ad-051.jpg','active'),
(1052,1026,'SEED-AD-052','Planejados região - B','image','Projeto personalizado','Fale com um especialista.','https://example.com/ads/ad-052.jpg','active'),
(1053,1027,'SEED-AD-053','Sala - A','carousel','Renove sua sala','Inspire-se com nossos móveis.','https://example.com/ads/ad-053.jpg','active'),
(1054,1027,'SEED-AD-054','Sala - B','image','Sua sala mais bonita','Confira nossas opções.','https://example.com/ads/ad-054.jpg','active'),
(1055,1028,'SEED-AD-055','Remarketing produtos - A','carousel','Você viu este produto','Confira novamente.','https://example.com/ads/ad-055.jpg','active'),
(1056,1028,'SEED-AD-056','Remarketing produtos - B','image','Ainda pensando no seu ambiente?','Veja nossas condições.','https://example.com/ads/ad-056.jpg','active'),
(1057,1029,'SEED-AD-057','Marca - A','responsive','Casa Norte Móveis','Conheça nossa loja.','https://example.com/ads/ad-057.jpg','active'),
(1058,1029,'SEED-AD-058','Marca - B','responsive','Móveis para sua casa','Qualidade e design.','https://example.com/ads/ad-058.jpg','active'),
(1059,1030,'SEED-AD-059','Visitantes - A','image','Encontre seu próximo móvel','Confira os destaques.','https://example.com/ads/ad-059.jpg','active'),
(1060,1030,'SEED-AD-060','Visitantes - B','video','Inspire seu próximo ambiente','Veja nossos projetos.','https://example.com/ads/ad-060.jpg','active'),
(1061,1031,'SEED-AD-061','Leads planejados - A','image','Planeje seu ambiente','Solicite um projeto.','https://example.com/ads/ad-061.jpg','active'),
(1062,1031,'SEED-AD-062','Leads planejados - B','image','Móveis sob medida','Fale com nossa equipe.','https://example.com/ads/ad-062.jpg','active'),
(1063,1032,'SEED-AD-063','Lookalike compradores - A','video','Projetos que combinam com você','Conheça nossas ideias.','https://example.com/ads/ad-063.jpg','active'),
(1064,1032,'SEED-AD-064','Lookalike compradores - B','image','Seu projeto começa aqui','Peça seu orçamento.','https://example.com/ads/ad-064.jpg','active'),
(1065,1033,'SEED-AD-065','Catálogo - A','carousel','Veja nossos produtos','Escolha seus favoritos.','https://example.com/ads/ad-065.jpg','active'),
(1066,1033,'SEED-AD-066','Catálogo - B','carousel','Produtos em destaque','Confira as novidades.','https://example.com/ads/ad-066.jpg','active'),
(1067,1034,'SEED-AD-067','Carrinho - A','image','Seu ambiente está quase pronto','Finalize seu pedido.','https://example.com/ads/ad-067.jpg','active'),
(1068,1034,'SEED-AD-068','Carrinho - B','image','Não deixe seu projeto para depois','Volte ao seu carrinho.','https://example.com/ads/ad-068.jpg','active'),
(1069,1035,'SEED-AD-069','Decoração - A','video','Inspire-se para decorar','Ideias para sua casa.','https://example.com/ads/ad-069.jpg','ended'),
(1070,1035,'SEED-AD-070','Decoração - B','image','Novas ideias para seu ambiente','Veja inspirações.','https://example.com/ads/ad-070.jpg','ended'),
(1071,1036,'SEED-AD-071','Engajamento - A','video','Inspiração para sua casa','Acompanhe nossas ideias.','https://example.com/ads/ad-071.jpg','ended'),
(1072,1036,'SEED-AD-072','Engajamento - B','image','Decore com personalidade','Veja nossos projetos.','https://example.com/ads/ad-072.jpg','ended'),

(1073,1037,'SEED-AD-073','Matrículas - A','image','Comece sua transformação','Conheça a FitLife.','https://example.com/ads/ad-073.jpg','active'),
(1074,1037,'SEED-AD-074','Matrículas - B','video','Matricule-se hoje','Treinos para seus objetivos.','https://example.com/ads/ad-074.jpg','active'),
(1075,1038,'SEED-AD-075','Interesse fitness - A','image','Sua melhor versão começa aqui','Conheça nossos planos.','https://example.com/ads/ad-075.jpg','active'),
(1076,1038,'SEED-AD-076','Interesse fitness - B','image','Treine com estrutura completa','Venha conhecer a academia.','https://example.com/ads/ad-076.jpg','active'),
(1077,1039,'SEED-AD-077','Personal - A','image','Treino personalizado','Acompanhamento para seus objetivos.','https://example.com/ads/ad-077.jpg','active'),
(1078,1039,'SEED-AD-078','Personal - B','video','Evolua com acompanhamento','Conheça nossos profissionais.','https://example.com/ads/ad-078.jpg','active'),
(1079,1040,'SEED-AD-079','Alta renda - A','image','Treino exclusivo','Experiência personalizada.','https://example.com/ads/ad-079.jpg','active'),
(1080,1040,'SEED-AD-080','Alta renda - B','video','Resultados com acompanhamento','Conheça o programa.','https://example.com/ads/ad-080.jpg','active'),
(1081,1041,'SEED-AD-081','Marca - A','responsive','FitLife Academia','Conheça nossa estrutura.','https://example.com/ads/ad-081.jpg','active'),
(1082,1041,'SEED-AD-082','Marca - B','responsive','Treine na FitLife','Faça uma visita.','https://example.com/ads/ad-082.jpg','active'),
(1083,1042,'SEED-AD-083','Visitantes - A','image','Volte para a FitLife','Conheça nossos planos.','https://example.com/ads/ad-083.jpg','active'),
(1084,1042,'SEED-AD-084','Visitantes - B','video','Seu treino está esperando','Agende uma visita.','https://example.com/ads/ad-084.jpg','active'),
(1085,1043,'SEED-AD-085','Leads matrícula - A','image','Matricule-se na FitLife','Fale com nossa equipe.','https://example.com/ads/ad-085.jpg','active'),
(1086,1043,'SEED-AD-086','Leads matrícula - B','video','Comece agora','Planos para diferentes objetivos.','https://example.com/ads/ad-086.jpg','active'),
(1087,1044,'SEED-AD-087','Lookalike alunos - A','image','Treine com quem entende','Conheça a FitLife.','https://example.com/ads/ad-087.jpg','active'),
(1088,1044,'SEED-AD-088','Lookalike alunos - B','image','Resultados começam aqui','Venha treinar conosco.','https://example.com/ads/ad-088.jpg','active'),
(1089,1045,'SEED-AD-089','Remarketing - A','image','Ainda pensando em começar?','Dê o primeiro passo.','https://example.com/ads/ad-089.jpg','active'),
(1090,1045,'SEED-AD-090','Remarketing - B','video','Seu plano está aqui','Fale com a FitLife.','https://example.com/ads/ad-090.jpg','active'),
(1091,1046,'SEED-AD-091','Engajamento - A','video','Treino e motivação','Acompanhe nossas dicas.','https://example.com/ads/ad-091.jpg','active'),
(1092,1046,'SEED-AD-092','Engajamento - B','image','Mais movimento no seu dia','Confira nossos conteúdos.','https://example.com/ads/ad-092.jpg','active'),
(1093,1047,'SEED-AD-093','Desafio - A','video','Desafio 30 Dias','Comece sua transformação.','https://example.com/ads/ad-093.jpg','ended'),
(1094,1047,'SEED-AD-094','Desafio - B','image','30 dias para mudar','Participe do desafio.','https://example.com/ads/ad-094.jpg','ended'),
(1095,1048,'SEED-AD-095','Remarketing desafio - A','video','Você pode continuar','Retome seu desafio.','https://example.com/ads/ad-095.jpg','ended'),
(1096,1048,'SEED-AD-096','Remarketing desafio - B','image','Não pare agora','Continue sua jornada.','https://example.com/ads/ad-096.jpg','ended'),

(1097,1049,'SEED-AD-097','Componentes - A','search','Componentes para PC','Encontre hardware para seu computador.','https://example.com/ads/ad-097.jpg','active'),
(1098,1049,'SEED-AD-098','Componentes - B','search','Peças para PC','Confira nossas opções.','https://example.com/ads/ad-098.jpg','active'),
(1099,1050,'SEED-AD-099','Hardware - A','image','Monte seu PC','Componentes selecionados.','https://example.com/ads/ad-099.jpg','active'),
(1100,1050,'SEED-AD-100','Hardware - B','image','Upgrade no seu computador','Veja as opções.','https://example.com/ads/ad-100.jpg','active'),
(1101,1051,'SEED-AD-101','Notebook gamer - A','image','Notebook gamer','Potência para jogar e trabalhar.','https://example.com/ads/ad-101.jpg','active'),
(1102,1051,'SEED-AD-102','Notebook gamer - B','video','Performance para seus jogos','Conheça nossos notebooks.','https://example.com/ads/ad-102.jpg','active'),
(1103,1052,'SEED-AD-103','Remarketing notebook - A','carousel','Você viu este notebook','Confira novamente.','https://example.com/ads/ad-103.jpg','active'),
(1104,1052,'SEED-AD-104','Remarketing notebook - B','image','Ainda procurando seu notebook?','Veja as condições.','https://example.com/ads/ad-104.jpg','active'),
(1105,1053,'SEED-AD-105','Marca - A','responsive','TechParts Brasil','Tecnologia e hardware.','https://example.com/ads/ad-105.jpg','active'),
(1106,1053,'SEED-AD-106','Marca - B','responsive','Tudo para seu setup','Conheça nossa loja.','https://example.com/ads/ad-106.jpg','active'),
(1107,1054,'SEED-AD-107','Visitantes - A','image','Volte para a TechParts','Confira nossos produtos.','https://example.com/ads/ad-107.jpg','active'),
(1108,1054,'SEED-AD-108','Visitantes - B','video','Seu próximo upgrade','Encontre seu hardware.','https://example.com/ads/ad-108.jpg','active'),
(1109,1055,'SEED-AD-109','Conversão - A','image','Compre seus componentes','Ofertas para seu setup.','https://example.com/ads/ad-109.jpg','active'),
(1110,1055,'SEED-AD-110','Conversão - B','carousel','Monte seu setup','Escolha seus componentes.','https://example.com/ads/ad-110.jpg','active'),
(1111,1056,'SEED-AD-111','Lookalike - A','image','Hardware para você','Produtos selecionados.','https://example.com/ads/ad-111.jpg','active'),
(1112,1056,'SEED-AD-112','Lookalike - B','video','Upgrade seu PC','Encontre o que precisa.','https://example.com/ads/ad-112.jpg','active'),
(1113,1057,'SEED-AD-113','Remarketing - A','carousel','Você ainda quer este produto?','Finalize sua compra.','https://example.com/ads/ad-113.jpg','active'),
(1114,1057,'SEED-AD-114','Remarketing - B','image','Seu carrinho espera por você','Volte para a loja.','https://example.com/ads/ad-114.jpg','active'),
(1115,1058,'SEED-AD-115','Clientes recorrentes - A','image','Ofertas para clientes','Confira novidades.','https://example.com/ads/ad-115.jpg','active'),
(1116,1058,'SEED-AD-116','Clientes recorrentes - B','image','Novos produtos no estoque','Veja os lançamentos.','https://example.com/ads/ad-116.jpg','active'),
(1117,1059,'SEED-AD-117','Ofertas - A','image','Ofertas da semana','Aproveite as oportunidades.','https://example.com/ads/ad-117.jpg','active'),
(1118,1059,'SEED-AD-118','Ofertas - B','carousel','Promoções TechParts','Confira os descontos.','https://example.com/ads/ad-118.jpg','active'),
(1119,1060,'SEED-AD-119','Social - A','video','Dicas para seu setup','Acompanhe a TechParts.','https://example.com/ads/ad-119.jpg','active'),
(1120,1060,'SEED-AD-120','Social - B','image','Tecnologia para seu dia','Veja nossos conteúdos.','https://example.com/ads/ad-120.jpg','active');

-- ============================================================
-- 6. MÉTRICAS DIÁRIAS
-- 3 dias por anúncio = 360 registros.
-- Os números são deliberadamente variados para permitir testes
-- de CTR, CPC, CPM, conversões e comparações.
-- ============================================================

INSERT IGNORE INTO daily_metrics
    (ad_id, metric_date, impressions, clicks, spend, reach, video_views,
     platform_conversions, platform_conversion_value)
SELECT
    a.id,
    d.metric_date,
    900 + ((a.id * 137 + DAY(d.metric_date) * 31) % 1800),
    25 + ((a.id * 17 + DAY(d.metric_date) * 5) % 90),
    ROUND(18 + ((a.id * 7 + DAY(d.metric_date) * 3) % 55) + (a.id % 4) * 2.5, 2),
    650 + ((a.id * 97 + DAY(d.metric_date) * 13) % 1000),
    CASE
        WHEN a.format = 'video' THEN 250 + ((a.id * 29 + DAY(d.metric_date) * 7) % 700)
        ELSE 0
    END,
    1 + ((a.id + DAY(d.metric_date)) % 8),
    ROUND((1 + ((a.id + DAY(d.metric_date)) % 8)) * (80 + (a.id % 5) * 35), 2)
FROM ads a
CROSS JOIN (
    SELECT DATE('2026-07-28') AS metric_date
    UNION ALL
    SELECT DATE('2026-07-29')
    UNION ALL
    SELECT DATE('2026-07-30')
) d
ORDER BY a.id, d.metric_date;

-- ============================================================
-- 7. LANDING PAGES
-- 2 por cliente = 10 registros.
-- ============================================================

INSERT IGNORE INTO landing_pages (id, client_id, name, url) VALUES
(1001,  1001, 'Captação de imóveis',        'https://example.com/alpha-imoveis/captacao'),
(1002,  1001, 'Apartamentos',               'https://example.com/alpha-imoveis/apartamentos'),
(1003,  1002, 'Avaliação odontológica',     'https://example.com/bella-odonto/avaliacao'),
(1004,  1002, 'Implantes',                   'https://example.com/bella-odonto/implantes'),
(1005,  1003, 'Móveis planejados',           'https://example.com/casa-norte/planejados'),
(1006,  1003, 'Catálogo',                    'https://example.com/casa-norte/catalogo'),
(1007,  1004, 'Matrícula',                   'https://example.com/fitlife/matricula'),
(1008,  1004, 'Planos',                      'https://example.com/fitlife/planos'),
(1009,  1005, 'Componentes',                 'https://example.com/techparts/componentes'),
(1010,  1005, 'Notebook gamer',              'https://example.com/techparts/notebook-gamer');

-- ============================================================
-- 8. LEADS
-- 50 leads, distribuídos entre os 5 clientes e campanhas.
-- ============================================================

INSERT IGNORE INTO leads
    (id, client_id, landing_page_id, campaign_id, ad_id, source,
     name, email, phone, status, created_at)
VALUES
(1001,1001,1001,1001,1001,'google_ads','Ana Martins','ana.martins@example.com','47991000001','converted','2026-07-28 09:12:00'),
(1002,1001,1001,1001,1002,'google_ads','Bruno Silva','bruno.silva@example.com','47991000002','qualified','2026-07-28 10:35:00'),
(1003,1001,1002,1004,1013,'meta_ads','Carla Souza','carla.souza@example.com','47991000003','contacted','2026-07-28 13:20:00'),
(1004,1001,1002,1004,1014,'meta_ads','Diego Alves','diego.alves@example.com','47991000004','converted','2026-07-29 08:45:00'),
(1005,1001,1001,1005,1017,'meta_ads','Elisa Costa','elisa.costa@example.com','47991000005','new','2026-07-29 11:05:00'),
(1006,1001,1001,1001,1003,'google_ads','Felipe Rocha','felipe.rocha@example.com','47991000006','lost','2026-07-29 15:42:00'),
(1007,1001,1002,1004,1015,'meta_ads','Gabriela Lima','gabriela.lima@example.com','47991000007','qualified','2026-07-30 09:18:00'),
(1008,1001,1001,1001,1004,'google_ads','Henrique Dias','henrique.dias@example.com','47991000008','converted','2026-07-30 14:10:00'),
(1009,1001,1002,1005,1018,'meta_ads','Isabela Ramos','isabela.ramos@example.com','47991000009','contacted','2026-07-30 16:32:00'),
(1010,1001,1001,1004,1016,'meta_ads','João Mendes','joao.mendes@example.com','47991000010','new','2026-07-30 17:05:00'),

(1011,1002,1003,1007,1025,'google_ads','Laura Martins','laura.martins@example.com','47992000001','converted','2026-07-28 08:15:00'),
(1012,1002,1004,1007,1026,'google_ads','Marcelo Nunes','marcelo.nunes@example.com','47992000002','qualified','2026-07-28 09:47:00'),
(1013,1002,1003,1010,1037,'meta_ads','Natália Souza','natalia.souza@example.com','47992000003','contacted','2026-07-28 11:22:00'),
(1014,1002,1004,1010,1038,'meta_ads','Otávio Lima','otavio.lima@example.com','47992000004','converted','2026-07-28 15:18:00'),
(1015,1002,1003,1011,1041,'meta_ads','Patrícia Alves','patricia.alves@example.com','47992000005','new','2026-07-29 08:33:00'),
(1016,1002,1003,1007,1027,'google_ads','Rafael Costa','rafael.costa@example.com','47992000006','lost','2026-07-29 12:44:00'),
(1017,1002,1004,1011,1042,'meta_ads','Sabrina Rocha','sabrina.rocha@example.com','47992000007','qualified','2026-07-29 14:11:00'),
(1018,1002,1003,1010,1039,'meta_ads','Thiago Dias','thiago.dias@example.com','47992000008','converted','2026-07-30 09:27:00'),
(1019,1002,1004,1007,1025,'google_ads','Vanessa Ramos','vanessa.ramos@example.com','47992000009','contacted','2026-07-30 13:09:00'),
(1020,1002,1003,1010,1040,'meta_ads','William Mendes','william.mendes@example.com','47992000010','new','2026-07-30 16:51:00'),

(1021,1003,1005,1013,1049,'google_ads','Alice Pereira','alice.pereira@example.com','47993000001','converted','2026-07-28 08:41:00'),
(1022,1003,1005,1013,1050,'google_ads','Bernardo Silva','bernardo.silva@example.com','47993000002','qualified','2026-07-28 10:03:00'),
(1023,1003,1006,1016,1061,'meta_ads','Camila Souza','camila.souza@example.com','47993000003','contacted','2026-07-28 11:58:00'),
(1024,1003,1005,1016,1062,'meta_ads','Daniel Costa','daniel.costa@example.com','47993000004','converted','2026-07-28 14:24:00'),
(1025,1003,1006,1017,1065,'meta_ads','Eduarda Lima','eduarda.lima@example.com','47993000005','new','2026-07-29 09:16:00'),
(1026,1003,1005,1013,1051,'google_ads','Fábio Rocha','fabio.rocha@example.com','47993000006','lost','2026-07-29 13:45:00'),
(1027,1003,1006,1016,1063,'meta_ads','Giovana Alves','giovana.alves@example.com','47993000007','qualified','2026-07-29 15:02:00'),
(1028,1003,1005,1014,1053,'google_ads','Hugo Dias','hugo.dias@example.com','47993000008','converted','2026-07-30 09:54:00'),
(1029,1003,1006,1017,1067,'meta_ads','Iara Mendes','iara.mendes@example.com','47993000009','contacted','2026-07-30 12:36:00'),
(1030,1003,1005,1016,1064,'meta_ads','Juliano Ramos','juliano.ramos@example.com','47993000010','new','2026-07-30 16:19:00'),

(1031,1004,1007,1019,1073,'google_ads','Amanda Martins','amanda.martins@example.com','47994000001','converted','2026-07-28 07:55:00'),
(1032,1004,1007,1019,1074,'google_ads','Bruno Costa','bruno.costa@example.com','47994000002','qualified','2026-07-28 10:16:00'),
(1033,1004,1008,1022,1085,'meta_ads','Clara Silva','clara.silva@example.com','47994000003','contacted','2026-07-28 12:07:00'),
(1034,1004,1007,1022,1086,'meta_ads','Davi Souza','davi.souza@example.com','47994000004','converted','2026-07-28 14:39:00'),
(1035,1004,1008,1023,1089,'meta_ads','Erika Lima','erika.lima@example.com','47994000005','new','2026-07-29 08:20:00'),
(1036,1004,1007,1019,1075,'google_ads','Fernando Alves','fernando.alves@example.com','47994000006','lost','2026-07-29 11:43:00'),
(1037,1004,1008,1022,1087,'meta_ads','Gustavo Rocha','gustavo.rocha@example.com','47994000007','qualified','2026-07-29 16:12:00'),
(1038,1004,1007,1020,1077,'google_ads','Helena Dias','helena.dias@example.com','47994000008','converted','2026-07-30 09:31:00'),
(1039,1004,1008,1023,1090,'meta_ads','Igor Ramos','igor.ramos@example.com','47994000009','contacted','2026-07-30 13:55:00'),
(1040,1004,1007,1022,1088,'meta_ads','Júlia Mendes','julia.mendes@example.com','47994000010','new','2026-07-30 17:02:00'),

(1041,1005,1009,1025,1097,'google_ads','André Martins','andre.martins@example.com','47995000001','converted','2026-07-28 08:07:00'),
(1042,1005,1010,1026,1101,'google_ads','Bianca Silva','bianca.silva@example.com','47995000002','qualified','2026-07-28 10:52:00'),
(1043,1005,1009,1028,1109,'meta_ads','Caio Souza','caio.souza@example.com','47995000003','contacted','2026-07-28 12:33:00'),
(1044,1005,1010,1028,1110,'meta_ads','Débora Costa','debora.costa@example.com','47995000004','converted','2026-07-28 15:26:00'),
(1045,1005,1009,1029,1113,'meta_ads','Eduardo Lima','eduardo.lima@example.com','47995000005','new','2026-07-29 09:41:00'),
(1046,1005,1009,1025,1098,'google_ads','Fernanda Rocha','fernanda.rocha@example.com','47995000006','lost','2026-07-29 13:17:00'),
(1047,1005,1010,1028,1111,'meta_ads','Guilherme Alves','guilherme.alves@example.com','47995000007','qualified','2026-07-29 15:48:00'),
(1048,1005,1009,1026,1102,'google_ads','Heloísa Dias','heloisa.dias@example.com','47995000008','converted','2026-07-30 10:05:00'),
(1049,1005,1010,1029,1114,'meta_ads','Isis Ramos','isis.ramos@example.com','47995000009','contacted','2026-07-30 14:27:00'),
(1050,1005,1009,1028,1112,'meta_ads','Joana Mendes','joana.mendes@example.com','47995000010','new','2026-07-30 16:44:00');

-- ============================================================
-- 9. CONVERSÕES
-- Algumas conversões são vendas/ações reais do negócio, não
-- necessariamente iguais às platform_conversions.
-- ============================================================

INSERT IGNORE INTO conversions
    (id, client_id, lead_id, campaign_id, type, value, conversion_date)
VALUES
(1001,  1001,  1001,  1001,  'appointment',  0.00,   '2026-07-28'),
(1002,  1001,  1004,  1004,  'purchase',  18500.00,  '2026-07-29'),
(1003,  1001,  1008,  1001,  'appointment', 0.00,    '2026-07-30'),
(1004,  1002,  1011,  1007,  'appointment', 0.00,    '2026-07-28'),
(1005,  1002,  1014,  1010,  'purchase',  4200.00,  '2026-07-28'),
(1006,  1002,  1018,  1010,  'appointment', 0.00,   '2026-07-30'),
(1007,  1003,  1021,  1013,  'appointment', 0.00,    '2026-07-28'),
(1008,  1003,  1024,  1016,  'purchase',  6800.00,  '2026-07-28'),
(1009,  1003,  1028,  1014,  'purchase',  5200.00,  '2026-07-30'),
(1010,  1003,  1029,  1017,  'appointment', 0.00,   '2026-07-30'),
(1011,  1004,  1031,  1019,  'signup', 0.00,         '2026-07-28'),
(1012,  1004,  1034,  1022,  'signup', 0.00,         '2026-07-28'),
(1013,  1004,  1038,  1020,  'purchase',  399.90,    '2026-07-30'),
(1014,  1005,  1041,  1025,  'purchase',  2899.90,   '2026-07-28'),
(1015,  1005,  1044,  1028,  'purchase',  4599.90,   '2026-07-28'),
(1016,  1005,  1048,  1026,  'purchase',  7299.90,   '2026-07-30'),
(1017,  1005,  1049,  1029,  'purchase',  1899.90,   '2026-07-30');

COMMIT;

-- ============================================================
-- RESUMO DO SEED
--
-- clients         = 5
-- ad_accounts     = 10
-- campaigns       = 30
-- ad_groups       = 60
-- ads             = 120
-- daily_metrics   = 360
-- landing_pages   = 10
-- leads           = 50
-- conversions     = 17
-- platforms       = já populada pelo schema.sql
-- schema_migrations= controlada pelo sistema de migrations
-- ============================================================
