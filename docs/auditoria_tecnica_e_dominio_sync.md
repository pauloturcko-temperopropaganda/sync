# Sync — Auditoria Técnica e de Domínio

---

## 1. Executive Summary

O **Sync** é uma plataforma analítica e operacional em estágio de **MVP**, projetada para atender às necessidades reais de uma agência de publicidade e marketing. Sua finalidade principal é integrar, normalizar e centralizar dados de múltiplas plataformas de mídia paga (iniciando por Google Ads e Meta Ads, com planos para LinkedIn Ads e TikTok Ads), combinando **dados estruturados de performance** (banco relacional) com o **conhecimento contextual e estratégico dos clientes** (armazenado em arquivos Markdown no Vault/Obsidian).

A presente auditoria realizou uma varredura minuciosa de ponta a ponta em todo o repositório, inspecionando schemas SQL, scripts de migração, seeds, integrações com APIs, ferramentas da IA, regras de segurança, documentações internas e estrutura de pastas.

### Principais Conclusões do Diagnóstico:
1. **Descompasso de Granularidade no Banco Atual**: O schema atual amarra todas as métricas diárias à tabela `ads` (`daily_metrics.ad_id`), ignorando que relatórios de plataformas como o Google Ads operam em diferentes níveis de agregação (campanha, grupo, anúncio, ação de conversão, dispositivo e geografia). Inserir dados de nível de campanha ou segmentações multidimensionais no modelo atual é inviável sem corromper a integridade ou gerar registros falsos.
2. **Ausência de Suporte Organizacional (Holding/Marcas)**: O modelo atual presume `1 cliente = 1 conta`, desconsiderando grupos econômicos ou holdings que gerenciam múltiplas marcas e contas de anúncio distintas.
3. **Desconexão entre Banco e Vault**: O banco de dados foi populado com seeds fictícios genéricos (`seed-alpha-imoveis`, `seed-bella-odonto`, etc.), enquanto o Vault do Obsidian possui 5 clientes reais e estruturados da agência (`hospital-de-olhos-videira`, `cardoso-empreendimentos`, `bragagnolo-advocacia`, `cantina-toscana`, `vigor-studio`). Isso inviabiliza análises contextuais cruzadas pela IA no estado atual.
4. **Acúmulo de Código Legado e Inconsistente**: Há scripts de teste com imports quebrados (`src/tests/test_data/seed_test_data.py`), queries vazias (`src/queries/clients.py`), dependências não declaradas no `requirements.txt` (como `google-ads`) e erros matemáticos em queries analíticas (como somar a métrica `reach` ao longo dos dias).
5. **Decisão Arquitetural Mandatória**: **RECRIAR O BANCO DO ZERO**. Por se tratar de um MVP em fase laboratorial sem dados de produção, refazer o schema agora para uma modelagem dimensional limpa (Fatos segregados por granularidade + Dimensões unificadas) eliminará 100% da dívida técnica estrutural sem custo de migração de dados legados.

---

## 2. Contexto do Produto

O Sync visa resolver os gargalos analíticos e operacionais do dia a dia da agência:
- **Centralização Multi-Plataforma**: Evitar a dispersão de dados entre painéis fechados (Google Ads, Meta Ads Manager, LinkedIn Campaign Manager).
- **Análise Comparativa Temporal Real**: Permitir a comparação direta entre períodos equivalentes (MoM, YoY) e entre campanhas encerradas e campanhas ativas para responder perguntas críticas como: *"Por que a campanha deste ano gerou 30% menos leads com o mesmo orçamento do ano passado?"*.
- **Diagnóstico de Causa-Raiz**: Analisar dimensões de impacto (custo por clique, saturação de criativos, mudança na distribuição de dispositivos, variação por tipo de conversão e concorrência).
- **União entre Performance e Contexto de Negócio**: Combinar os números brutos do banco com as diretrizes do cliente registradas no Vault (restrições éticas da OAB para escritórios jurídicos, posicionamento de alto padrão para incorporadoras, restrições médicas para hospitais de olhos, etc.).
- **Habilitação de Inteligência Artificial**: Criar uma base confiável e granular para que modelos de linguagem (LLMs) possam atuar como analistas de mídia, gerando relatórios executivos, resumos de performance e recomendações táticas sem risco de alucinação de métricas.

---

## 3. Princípios e Decisões de Domínio

Classificação das premissas e decisões identificadas no projeto:

| Decisão / Premissa | Classificação | Justificativa / Situação Real |
| :--- | :--- | :--- |
| Separação Conhecimento (Vault) vs Dados Estruturados (DB) | **Confirmada pelo domínio** | O Vault guarda briefing, tom de voz e personas; o DB guarda métricas diárias e dados de campanhas. |
| Acesso somente leitura para Agente de IA | **Confirmada pelo código** | Implementado via usuário restrito (`sync_ai`) e scripts dedicados em `src/ai_tools/`. |
| Hierarquia `Organization -> Client/Brand -> Ad Account` | **Confirmada pelo domínio** | Necessário para grupos empresariais com múltiplas marcas e contas independentes. |
| Métricas diárias vinculadas unicamente ao Anúncio (`ads`) | **Potencialmente incorreta** | Nem todo relatório ou plataforma entrega dados no grão de anúncio; quebra queries de campanha/dispositivo/geografia. |
| Inclusão de tabelas de CRM (`landing_pages`, `leads`, `conversions`) | **Provisória / Possível legado** | Prematuro para o MVP de mídia; misturar CRM manual com ingestão de anúncios antes de validar APIs polui o schema. |
| Cálculo dinâmico de métricas derivadas (CTR, CPC, CPM) | **Confirmada pelo código** | Evita inconsistências de arredondamento salvando apenas fatos brutos (`impressions`, `clicks`, `cost_micros`). |
| Ingestão direta via scripts de impressão em terminal | **Provisória** | Scripts atuais do Google Ads apenas imprimem no terminal; falta o pipeline de persistência e upsert idempotente. |

---

## 4. Stack Tecnológica

- **Linguagem**: Python `3.13.15` (ambiente Windows).
- **Driver de Banco**: `PyMySQL 1.2.0` com cursores de dicionário (`DictCursor`).
- **Banco de Dados**: MariaDB / MySQL (`sync_db` em `localhost:3306`).
- **SDKs de Plataforma**:
  - Google Ads: `google-ads 31.2.0` (suportando chamadas gRPC/Protobuf via `GoogleAdsService`).
  - Autenticação Google: `google-auth 2.56.3`, `google-auth-oauthlib 1.4.0`, `requests-oauthlib 2.0.0`.
- **Gerenciamento de Ambiente**: `python-dotenv 1.2.2`.
- **Formatação e Validação**: Saídas formatadas em JSON puro via `json.dumps()` com conversor customizado para datas e objetos `Decimal`.
- **Base de Conhecimento**: Markdown estruturado no Vault (compatível com Obsidian).
- **Controle de Versão**: Git.

### Diagrama de Conexão da Stack:

```text
[ Obsidian / Vault (Markdown) ]
              │ (Contexto & Estratégia)
              ▼
    [ Agente de IA ] ◄─── (Executa Ferramenta) ─── [ src/ai_tools/*.py ]
                                                           │ (PyMySQL - sync_ai)
                                                           ▼
                                                  [ MariaDB: sync_db ]
                                                           ▲
                                                           │ (PyMySQL - sync_admin)
[ Google Ads / Meta Ads API ] ───► [ Ingestion Pipeline ] ─┘
```

---

## 5. Estrutura do Repositório

```text
c:\dev\sync\
├── .agents/
│   └── rules/
│       └── sync-ai-safety.md              # Regra de segurança persistente para agentes
├── .env.admin                             # Variáveis de ambiente e secrets de admin/APIs
├── .env.agent                             # Credenciais restritas (read-only) da IA
├── .env.example                           # Template documentando variáveis necessárias
├── .gitignore                             # Ignora venv, envs sensíveis, pycache e temporários
├── AI_GUIDE.md                            # Guia operacional mestre e catálogo de ferramentas
├── prompt_auditoria_completa_projeto_sync.md # Especificação mestre desta auditoria
├── requirements.txt                       # Arquivo de dependências (incompleto no estado atual)
├── schema.sql                             # DDL do schema atual (cópia raiz)
├── seed_safe.sql                          # Dados fictícios de teste com IDs >= 1001
├── src/
│   ├── ai_tools/                          # Ferramentas Python homologadas para a IA
│   │   ├── db.py                          # Conexão read-only segura via .env.agent
│   │   ├── get_client_info.py             # Consulta dados cadastrais do cliente
│   │   ├── get_client_campaigns.py        # Lista campanhas e contas de um cliente
│   │   ├── get_campaign_performance.py    # Agrega performance de uma campanha no período
│   │   └── get_client_conversions.py      # Lista conversões registradas no período
│   ├── db/
│   │   ├── admin.py                       # Conexão administrativa (DDL/DML) via .env.admin
│   │   └── run_migrations.py              # Runner de migrations sequenciais
│   ├── integrations/
│   │   ├── google_ads/                    # Integração com Google Ads API
│   │   │   ├── client.py                  # Fábrica do GoogleAdsClient e teste geo
│   │   │   ├── generate_refresh_token.py  # Script OAuth2 local para obter refresh token
│   │   │   ├── metrics.py                 # Query de métricas diárias de campanha
│   │   │   ├── test_connection.py         # Teste de listagem de contas acessíveis
│   │   │   ├── test_hierarchy.py          # BFS para mapear árvore de contas da MCC
│   │   │   ├── test_campaigns.py          # Listagem de campanhas por Customer ID
│   │   │   └── test_metrics.py            # Execução de teste de métricas diárias
│   │   └── meta_ads/                      # Diretório vazio (aguardando liberação e testes)
│   ├── migrations/
│   │   └── 0001_initial_schema.sql        # Migration inicial espelhando schema.sql
│   ├── queries/
│   │   └── clients.py                     # Arquivo vazio (legado)
│   └── tests/
│       ├── test_connection.py             # Teste de conectividade básica com o banco
│       └── test_data/
│           ├── query_test_data.py         # Script legado de consulta (imports quebrados)
│           └── seed_test_data.py          # Script legado de inserção (imports quebrados)
└── vault/
    └── Sync/
        └── clientes/                      # Conhecimento estruturado de 5 clientes reais
            ├── bragagnolo-advocacia/
            ├── cantina-toscana/
            ├── cardoso-empreendimentos/
            ├── hospital-de-olhos-videira/
            └── vigor-studio/
```

---

## 6. Arquitetura Atual

A arquitetura atual foi construída orientada a duas personas de execução:
1. **Administrador / Engenheiro de Dados**:
   - Opera via `.env.admin`.
   - Executa migrations através de `src/db/run_migrations.py`.
   - Autentica-se nas APIs externas (Google Ads) para testes e extração.
2. **Agente de IA (Read-Only)**:
   - Opera estritamente via `.env.agent` com usuário de permissão `SELECT` (`sync_ai`).
   - Não possui autorização nem capacidade de executar SQL livre.
   - Comunica-se exclusivamente chamando módulos CLI em `src/ai_tools/` que recebem parâmetros de negócio sanitizados e retornam JSON puro.

### Fluxo de Execução Atual:

```text
[ Pergunta do Usuário ]
          │
          ▼
[ Agente de IA consulta AI_GUIDE.md ]
          │
          ├──────────────────────────────────────────────┐
          ▼                                              ▼
[ Consulta Contextual ]                        [ Consulta Quantitativa ]
          │                                              │
          ▼                                              ▼
[ Leitura de Arquivo Markdown no Vault ]       [ Executa python -m src.ai_tools.<tool> ]
          │                                              │
          │                                              ▼
          │                                    [ Query SQL Parametrizada ]
          │                                              │
          │                                              ▼
          │                                    [ MariaDB (sync_db) ]
          │                                              │
          │                                              ▼
          │                                    [ Retorno JSON Estruturado ]
          │                                              │
          └───────────────────────┬──────────────────────┘
                                  │
                                  ▼
                     [ Resposta Consolidada ]
```

---

## 7. Banco de Dados Atual

Análise detalhada de todas as 11 tabelas definidas em `schema.sql` e `0001_initial_schema.sql`:

### 7.1. `clients`
- **Propósito**: Cadastrar os clientes da agência.
- **Granularidade**: 1 linha = 1 cliente atendido.
- **Colunas**: `id` (INT PK AI), `name` (VARCHAR 150 NN), `slug` (VARCHAR 150 NN UQ), `industry` (VARCHAR 100), `status` (ENUM('active','inactive') NN DEF 'active'), `created_at` (DATETIME NN), `updated_at` (DATETIME NN).
- **Problema**: Assume cliente como topo da cadeia; não há entidade `organizations` para gerenciar holdings com múltiplas marcas.

### 7.2. `platforms`
- **Propósito**: Tabela lookup de plataformas de anúncios suportadas.
- **Granularidade**: 1 linha = 1 plataforma (`google_ads`, `meta_ads`, `linkedin_ads`, `tiktok_ads`).
- **Colunas**: `id` (INT PK AI), `name` (VARCHAR 50 NN), `slug` (VARCHAR 50 NN UQ).

### 7.3. `ad_accounts`
- **Propósito**: Contas de anúncio vinculadas ao cliente.
- **Granularidade**: 1 linha = 1 conta em uma plataforma para um cliente.
- **Colunas**: `id` (INT PK AI), `client_id` (INT FK NN -> `clients.id`), `platform_id` (INT FK NN -> `platforms.id`), `external_account_id` (VARCHAR 100 NN), `name` (VARCHAR 150), `currency` (CHAR 3 DEF 'BRL'), `timezone` (VARCHAR 50 DEF 'America/Sao_Paulo'), `status` (ENUM NN), `created_at`, `updated_at`.
- **Constraint**: `UNIQUE KEY uq_account_platform (platform_id, external_account_id)`.

### 7.4. `campaigns`
- **Propósito**: Campanhas criadas nas contas de anúncio.
- **Granularidade**: 1 linha = 1 campanha em uma conta de anúncio.
- **Colunas**: `id` (INT PK AI), `ad_account_id` (INT FK NN -> `ad_accounts.id`), `external_campaign_id` (VARCHAR 100 NN), `name` (VARCHAR 200 NN), `objective` (VARCHAR 50), `status` (ENUM('active','paused','ended','draft') NN), `budget_type` (ENUM('daily','lifetime')), `budget_amount` (DECIMAL 12,2), `start_date` (DATE), `end_date` (DATE), `created_at`, `updated_at`.
- **Constraint**: `UNIQUE KEY uq_campaign_account (ad_account_id, external_campaign_id)`.

### 7.5. `ad_groups`
- **Propósito**: Grupos de anúncios (Google) ou Conjuntos de anúncios (Meta Ad Sets).
- **Granularidade**: 1 linha = 1 grupo/conjunto em uma campanha.
- **Colunas**: `id` (INT PK AI), `campaign_id` (INT FK NN -> `campaigns.id`), `external_ad_group_id` (VARCHAR 100 NN), `name` (VARCHAR 200 NN), `status` (ENUM NN), `targeting_summary` (TEXT), `created_at`, `updated_at`.
- **Constraint**: `UNIQUE KEY uq_adgroup_campaign (campaign_id, external_ad_group_id)`.

### 7.6. `ads`
- **Propósito**: Peças criativas e anúncios individuais.
- **Granularidade**: 1 linha = 1 anúncio em um ad group.
- **Colunas**: `id` (INT PK AI), `ad_group_id` (INT FK NN -> `ad_groups.id`), `external_ad_id` (VARCHAR 100 NN), `name` (VARCHAR 200), `format` (VARCHAR 50), `headline` (VARCHAR 255), `description` (TEXT), `creative_url` (VARCHAR 500), `status` (ENUM NN), `created_at`, `updated_at`.
- **Constraint**: `UNIQUE KEY uq_ad_adgroup (ad_group_id, external_ad_id)`.

### 7.7. `daily_metrics` (Ponto Crítico de Falha de Modelagem)
- **Propósito**: Armazenar métricas diárias agregadas por anúncio.
- **Granularidade Declarada**: `ad_id + metric_date`.
- **Colunas**: `id` (BIGINT PK AI), `ad_id` (INT FK NN -> `ads.id`), `metric_date` (DATE NN), `impressions` (INT NN DEF 0), `clicks` (INT NN DEF 0), `spend` (DECIMAL 12,2 NN DEF 0), `reach` (INT), `video_views` (INT), `platform_conversions` (INT NN DEF 0), `platform_conversion_value` (DECIMAL 12,2 NN DEF 0), `created_at` (DATETIME NN).
- **Constraint**: `UNIQUE KEY uq_metric_ad_date (ad_id, metric_date)`.
- **Falha Estrutural**: Incompatível com métricas que só existem no nível da campanha ou que possuem segmentações ortogonais (Dispositivo, Geografia, Ação de Conversão).

### 7.8. `landing_pages`
- **Propósito**: Registro de URLs de destino para atribuição de leads.
- **Granularidade**: 1 linha = 1 página de destino de um cliente.
- **Colunas**: `id` (INT PK AI), `client_id` (INT FK NN), `name` (VARCHAR 150), `url` (VARCHAR 500 NN), `created_at`.

### 7.9. `leads`
- **Propósito**: Contatos capturados vinculados a campanhas/anúncios.
- **Granularidade**: 1 linha = 1 lead individual.
- **Colunas**: `id` (BIGINT PK AI), `client_id` (INT FK NN), `landing_page_id` (INT FK), `campaign_id` (INT FK), `ad_id` (INT FK), `source` (VARCHAR 50), `name` (VARCHAR 150), `email` (VARCHAR 150), `phone` (VARCHAR 30), `status` (ENUM('new','contacted','qualified','converted','lost') NN), `created_at`, `updated_at`.

### 7.10. `conversions`
- **Propósito**: Conversões de negócio (compras, agendamentos, MQLs).
- **Granularidade**: 1 linha = 1 evento de conversão de negócio.
- **Colunas**: `id` (BIGINT PK AI), `client_id` (INT FK NN), `lead_id` (BIGINT FK), `campaign_id` (INT FK), `type` (VARCHAR 50 NN), `value` (DECIMAL 12,2 DEF 0), `conversion_date` (DATE NN), `created_at`.

### 7.11. `schema_migrations`
- **Propósito**: Controle de execução de migrations versionadas.
- **Granularidade**: 1 linha = 1 script SQL executado.
- **Colunas**: `id` (INT PK AI), `filename` (VARCHAR 255 NN UQ), `applied_at` (DATETIME NN).

---

## 8. Migrations e Seeds

### 8.1. Análise de Migrations
- Existe apenas uma migration versionada: `src/migrations/0001_initial_schema.sql`, idêntica ao `schema.sql` da raiz.
- O runner `src/db/run_migrations.py` divide o arquivo por `;` e executa instrução por instrução.
- **Vulnerabilidade no runner**: O script faz um split ingênuo em `;`. Se houver `;` dentro de strings literais ou triggers/procedures, a execução falhará.

### 8.2. Análise de Seeds (`seed_safe.sql`)
- Foram inseridos dados puramente fictícios com IDs a partir de `1001` para 5 empresas genéricas:
  - Alpha Imóveis (`seed-alpha-imoveis`)
  - Bella Odonto (`seed-bella-odonto`)
  - Casa Norte Móveis (`seed-casa-norte-moveis`)
  - FitLife Academia (`seed-fitlife-academia`)
  - TechParts Brasil (`seed-techparts-brasil`)
- Total inserido: 5 clientes, 10 contas de anúncio, 30 campanhas, 60 ad groups, 120 ads, 360 métricas diárias, 10 landing pages, 50 leads e 17 conversões.
- **Problema Crítico Identificado**: Os dados do seed mascaram a ausência do pipeline real de ingestão e não possuem nenhuma correlação com os 5 clientes reais do Vault (`hospital-de-olhos-videira`, etc.).

---

## 9. Google Ads

A investigação nos scripts de `src/integrations/google_ads/` revelou o status exato da integração:

### 9.1. Autenticação e Topologia
- **Autenticação**: OAuth2 via `InstalledAppFlow` gerando `refresh_token` offline persistido em `.env.admin`.
- **MCC (Manager Account)**: `8934723647` (`GOOGLE_ADS_LOGIN_CUSTOMER_ID`).
- **Conta de Teste/Produção**: `4378571170` (`GOOGLE_ADS_CUSTOMER_ID`).
- **Versão da API**: `google-ads 31.2.0` (executando chamadas gRPC na versão v18/v19 da API).

### 9.2. Endpoints e Recursos Validados no Código
1. **Hierarquia MCC (`customer_client`)**:
   - `test_hierarchy.py` implementa uma busca em largura (BFS) a partir da conta gerente `8934723647`, mapeando IDs, nomes descritivos, moedas e fusos horários de todas as contas subordinadas.
2. **Listagem de Campanhas (`campaign`)**:
   - `test_campaigns.py` consulta `campaign.id`, `campaign.name`, `campaign.status`, `campaign.advertising_channel_type`.
3. **Métricas Diárias de Campanha (`campaign` + `segments.date`)**:
   - `metrics.py` consulta métricas no grão `campaign + date`:
     - Contagens: `impressions`, `clicks`, `conversions`.
     - Valores: `cost_micros` (convertido para moeda dividindo por 1.000.000).
     - Derivadas: `ctr`, `average_cpc`, `cost_per_conversion`.
4. **Visão Geográfica (`geographic_view`)**:
   - `client.py` consulta `geographic_view.country_criterion_id` juntamente com `campaign.id` e `segments.date`.
   - **Erro documentado superado**: Foi constatado que misturar campos de `ad_group_ad` na cláusula `FROM geographic_view` gera erro fatal na API do Google por incompatibilidade de recursos. A query isolada em `geographic_view` funciona perfeitamente.
5. **Dimensões Adicionais Validadas**:
   - `segments.device` (retorna enums como `MOBILE`, `DESKTOP`, `TABLET`).
   - `segments.conversion_action` (retorna linhas individuais para cada ação de conversão configurada na conta).

---

## 10. Meta Ads

- **Status Atual**: Diretório `src/integrations/meta_ads/` está vazio.
- **Contexto Operacional**:
  - Houve bloqueio preventivo de dispositivo no cadastro do *Meta for Developers*.
  - O acesso ao painel `dev.meta.ai` não substitui a criação de App no *Meta for Developers* (`developers.facebook.com`).
  - A agência possui estrutura de *Business Portfolio*, aguardando atribuição de permissões ao usuário.
- **Diretriz Técnica**:
  - Nenhum schema ou payload da Meta deve ser inventado ou presumido antes da extração de respostas JSON reais via Postman / Graph API (`v20.0` ou superior).
  - A entidade equivalente a *Ad Group* no Meta Ads é o **Ad Set** (Conjunto de Anúncios), e o grão de métricas é obtido via endpoint `/insights`.

---

## 11. LinkedIn Ads e TikTok Ads

- **Status Atual**: Baixa prioridade / Planejamento futuro.
- **Presença no Código**: Apenas registros na tabela lookup `platforms` (`linkedin_ads`, `tiktok_ads`).
- **Diretriz Técnica**: Não criar abstrações prematuras baseadas nessas plataformas. A modelagem deve focar no núcleo Google Ads + Meta Ads, mantendo o design desacoplado e extensível.

---

## 12. Granularidade das Métricas (Análise de Fatos)

A falha central do modelo atual foi tentar forçar todos os dados analíticos na tabela `daily_metrics` vinculada ao anúncio. A tabela abaixo expõe os grãos reais das consultas das plataformas:

| Fato / Relatório | Grão Real (Chave Natural) | Compatível com `daily_metrics` atual? | Motivo da Incompatibilidade |
| :--- | :--- | :--- | :--- |
| **Performance de Campanha** | `ad_account_id + external_campaign_id + date` | **NÃO** | Exige `ad_id NOT NULL`, mas métricas de campanha não pertencem a um único anúncio. |
| **Performance de Anúncio** | `ad_account_id + ad_id + date` | **SIM** | Grão equivalente à tabela atual. |
| **Ações de Conversão** | `campaign_id + date + conversion_action_name` | **NÃO** | Uma campanha em uma data gera múltiplas linhas (ex: 5 cliques em WhatsApp, 2 compras). |
| **Segmentação por Dispositivo** | `campaign_id + date + device` | **NÃO** | A tabela atual não possui coluna `device` e duplicaria linhas se mantivesse a chave única atual. |
| **Segmentação Geográfica** | `campaign_id + date + country_id/region_id` | **NÃO** | Recurso incompatível com anúncios na API; exige tabela fato dedicada. |

---

## 13. Histórico versus Dados Vivos

Para atender ao caso de uso crítico da agência com alta performance e baixo custo de requisições de API, propõe-se a seguinte estratégia:

```text
[ Campanhas Ativas (Últimos 7-30 dias) ] ──► Sincronização Incremental Diária (Upsert no Banco)
[ Campanhas Encerradas (Histórico) ]     ──► Snapshot Persistido Definitivo (Imutável)
[ Consultas Analíticas e IA ]            ──► Leitura 100% no Banco de Dados Local
```

- **Campanhas Ativas**: Como as plataformas de anúncio ajustam retroativamente conversões e custos dos últimos dias (atribuição tardia e validação de cliques inválidos), o sistema deve sincronizar diariamente uma janela deslizante (ex: últimos 7 dias) via `INSERT ... ON DUPLICATE KEY UPDATE`.
- **Campanhas Encerradas / Históricas**: Uma vez que o período foi encerrado e a janela de atribuição fechou, os dados tornam-se fatos históricos imutáveis no banco, servindo de base permanente para comparações YoY e análises de IA sem consumir cotas de API.

---

## 14. Caso de Uso Crítico: Comparação Histórica

Para responder à pergunta da agência:
> *“Por que a campanha atual está performando pior que a campanha do mesmo período do ano passado?”*

O sistema deve permitir decompor a variação de resultado através da **Fórmula Fundamental de Performance de Mídia**:

$$\text{Conversões} = \text{Investimento} \times \left(\frac{1}{\text{CPC}}\right) \times \text{Taxa de Conversão}$$

O banco de dados precisa suportar a comparação isolada de cada fator causador:
1. **Fator Custo**: O CPC aumentou devido à concorrência? (Verificado em `cost_micros / clicks`).
2. **Fator Criativo**: O CTR caiu indicando saturação do anúncio? (Verificado em `clicks / impressions`).
3. **Fator Plataforma/Dispositivo**: O tráfego migrou de Desktop para Mobile reduzindo a conversão da landing page? (Verificado na segmentação por `device`).
4. **Fator Mix de Conversão**: A campanha gerou volume em conversões secundárias (visualizações) em vez da ação principal (compras)? (Verificado no grão de `conversion_action`).

O modelo atual não permite realizar essas análises de causa-raiz porque não possui segmentações por dispositivo nem ações de conversão segregadas.

---

## 15. Inteligência Artificial (IA)

O ecossistema de IA do Sync foi desenhado com foco rigoroso em **segurança determinística e ausência de alucinação**:
- A IA não acessa o banco via SQL livre.
- A IA aciona ferramentas CLI parametrizadas que realizam consultas agregadas.
- A IA cruza o resultado numérico do banco com o conhecimento contextual do cliente no Vault.

### Exemplo de Diagnóstico com a Estrutura Correta:
- **Dado Estruturado (DB)**: Campanha de Implantes do cliente *Hospital de Olhos Videira* teve aumento de 45% no CPC e queda de 30% em conversões em agosto/2026 vs agosto/2025.
- **Contexto (Vault)**: Arquivo `reunioes/29-07-2026.md` relata mudança de público-alvo para focar em familiares decisores com maior renda.
- **Parecer da IA**: *"A queda no volume de conversões decorre do afunilamento intencional de público definido na reunião de 29/07, que elevou o CPC mas aumentou a qualificação do lead."*

---

## 16. Multi-Plataforma: Entidades Comuns vs Específicas

| Entidade | Google Ads | Meta Ads | LinkedIn Ads | Tratamento no Domínio Sync |
| :--- | :--- | :--- | :--- | :--- |
| **Conta** | Customer ID (`123-456-7890`) | Act Account (`act_123456`) | Account ID | **Comum**: `ad_accounts` |
| **Nível 1** | Campaign | Campaign | Campaign Group / Campaign | **Comum**: `campaigns` |
| **Nível 2** | Ad Group | Ad Set | Campaign | **Comum**: `ad_groups` (ou `ad_sets`) |
| **Nível 3** | Ad (Responsive Search, etc.) | Ad (Creative) | Creative | **Comum**: `ads` |
| **Métricas Básicas** | Impr, Clicks, Cost, Conv | Impr, Clicks, Spend, Actions | Impr, Clicks, Spend, Leads | **Comum**: Fatos normalizados |
| **Ações de Conversão** | Conversion Action Category | Custom Conversions / Pixels | Conversion Events | **Específica / Normalizada por Nome** |
| **Geografia** | Criteria ID (Geo Target) | Country/Region Keys | Geo URNs | **Específica por plataforma** |

---

## 17. Segurança

1. **Segregação de Privilégios**:
   - `sync_admin`: Usuário com privilégios DDL/DML para executar migrations e rotinas de sincronização.
   - `sync_ai`: Usuário estritamente com `GRANT SELECT` nas tabelas necessárias.
2. **Proteção de Secrets**:
   - As credenciais sensíveis (OAuth Client Secret, Developer Token, Refresh Token) ficam isoladas em `.env.admin`, que está no `.gitignore`.
3. **Injeção de SQL**:
   - Todos os scripts em `src/ai_tools/` e `src/db/` utilizam consultas parametrizadas com tuplas de substituição (`%s`), eliminando riscos de SQL Injection.

---

## 18. Testes e Cobertura

- **Testes Existentes**:
  - `src/tests/test_connection.py`: Testa conexão básica (`SELECT 1`).
  - `src/integrations/google_ads/test_*.py`: Scripts de teste manual para chamadas na API do Google Ads.
- **Testes Quebrados Encontrados**:
  - `src/tests/test_data/seed_test_data.py`: Falha fatal por tentar importar módulos inexistentes (`db.connection`, `db.queries.clients`).
  - `src/tests/test_data/query_test_data.py`: Falha por tentar importar `db.connection` e sintaxe incompatível de cursor.
- **Recomendação para o MVP**:
  - Implementar testes unitários automatizados com `pytest` para as ferramentas de IA (`src/ai_tools/`), garantindo que validações de data, slugs inválidos e parâmetros vazios retornem os códigos de erro JSON esperados.

---

## 19. Dívida Técnica

### Crítica (Bloqueante para o Domínio e Ingestão)
- **Granularidade incorreta em `daily_metrics`**: Impede a persistência de dados no nível de campanha, ações de conversão, dispositivos e dados geográficos.
- **Ausência de Pipeline de Ingestão**: As integrações atuais do Google Ads apenas imprimem strings formatadas no console; não há lógica de gravação no banco.

### Alta (Afeta a Evolução do MVP)
- **Incompatibilidade de Slugs (DB vs Vault)**: Seeds usam nomes fictícios (`seed-alpha-imoveis`) e o Vault usa clientes reais (`hospital-de-olhos-videira`), impossibilitando testes reais de IA.
- **Dependências Ausentes no `requirements.txt`**: `google-ads`, `google-auth`, etc., não estão listados no arquivo.
- **Soma Inválida de `reach`**: `src/ai_tools/get_campaign_performance.py` faz `SUM(daily_metrics.reach)`, violando conceitos matemáticos de alcance em mídia.

### Média (Ajustes de Qualidade)
- Scripts de teste quebrados em `src/tests/test_data/`.
- Arquivo `src/queries/clients.py` vazio.
- Split ingênuo em `;` no executor de migrations `src/db/run_migrations.py`.

---

## 20. Problemas Encontrados (Resumo Consolidado)

1. `daily_metrics` amarra métricas a `ad_id`, impedindo salvar relatórios de campanha diretamente do Google Ads.
2. Inexistência da entidade `organizations` para agrupar clientes por holding/grupo econômico.
3. Desconexão total entre os clientes do Vault e os clientes do banco de dados.
4. Queries de ferramentas de IA (`get_campaign_performance.py`) retornam erro caso a campanha não tenha métricas no período devido a `INNER JOIN` em vez de `LEFT JOIN`.
5. `SUM(reach)` executado em agregação de performance.
6. Falta de suporte a `cost_micros` no banco (conversão prematura para `DECIMAL(12,2)`).
7. Ausência de tabela para ações de conversão e segmentações de dispositivo/geografia.

---

## 21. Conhecido vs Desconhecido

### Confirmado (Fatos Validados)
- Autenticação Google Ads via OAuth2 e conexão gRPC funcionam perfeitamente na conta `4378571170` subordinada à MCC `8934723647`.
- Extração de métricas de campanha (`impressions`, `clicks`, `cost_micros`, `conversions`) validada.
- Extração de dimensões `device`, `conversion_action` e `geographic_view` validada no Google Ads.
- Modelo de isolamento de segurança da IA (read-only via JSON) validado e funcional.

### Inferido (Conclusões Lógicas)
- A Meta Ads API entregará estrutura hierárquica similar (Account -> Campaign -> AdSet -> Ad) com métricas correspondentes via endpoint Insights.
- A modelagem dimensional com Fatos segregados resolve 100% dos problemas de granularidade observados.

### Desconhecido (Ainda Não Testado)
- Payloads reais da Meta Ads Graph API para as contas da agência.
- Comportamento de cotas e rate limits sob sincronização massiva de histórico.

### Hipóteses
- Uma janela deslizante de 7 dias de ressincronização é suficiente para capturar a quase totalidade das conversões tardias nas plataformas.

### Próximas Validações
- Realizar chamada na Meta Graph API via Postman/cURL assim que o acesso ao Business Portfolio for liberado.
- Validar query de `geographic_view` com mapeamento dos nomes de cidades/estados via `geo_target_constant`.

---

## 22. Modelo de Domínio Proposto

O modelo conceitual refinado deve refletir com exatidão a realidade da agência:

```text
[ Organization / Holding ] (1)
       │
       ▼ (N)
[ Client / Brand ] (1) ◄────── Identificado pelo "slug" correspondente no Vault
       │
       ▼ (N)
[ Ad Account ] (1) ─────────── Plataforma (Google Ads, Meta Ads, etc.)
       │
       ▼ (N)
[ Campaign ] (1)
       │
       ├──────────────────────────────────────────┐
       ▼ (N)                                      ▼ (N)
  [ Ad Group / Ad Set ] (1)             [ Fact Tables por Granularidade ]
       │                                 ├── fact_campaign_daily_metrics
       ▼ (N)                             ├── fact_campaign_device_metrics
     [ Ad ]                              └── fact_campaign_conversion_actions
       │
       ▼ (N)
[ fact_ad_daily_metrics ]
```

---

## 23. Banco de Dados Proposto (Schema Refinado)

### 23.1. Tabelas de Cadastro e Hierarquia

#### Tabela: `organizations`
- **Propósito**: Agrupar clientes pertencentes à mesma holding ou grupo econômico.
- **Granularidade**: 1 linha = 1 organização proprietária.
- **PK**: `id` (INT AUTO_INCREMENT)
- **Colunas**: `name` (VARCHAR(150) NOT NULL), `slug` (VARCHAR(150) NOT NULL UNIQUE), `created_at` (DATETIME NOT NULL).

#### Tabela: `clients`
- **Propósito**: Representa a marca ou empresa atendida pela agência (chave de sincronização com o Vault).
- **Granularidade**: 1 linha = 1 cliente/marca.
- **PK**: `id` (INT AUTO_INCREMENT)
- **FKs**: `organization_id` -> `organizations(id)` (NULLABLE para clientes sem holding).
- **Colunas**: `organization_id` (INT), `name` (VARCHAR(150) NOT NULL), `slug` (VARCHAR(150) NOT NULL UNIQUE), `industry` (VARCHAR(100)), `status` (ENUM('active','inactive') NOT NULL DEFAULT 'active'), `created_at`, `updated_at`.

#### Tabela: `platforms`
- **Propósito**: Lookup de plataformas suportadas.
- **PK**: `id` (INT AUTO_INCREMENT)
- **Colunas**: `name` (VARCHAR(50) NOT NULL), `slug` (VARCHAR(50) NOT NULL UNIQUE).

#### Tabela: `ad_accounts`
- **Propósito**: Contas de anúncio nas plataformas vinculadas a uma marca.
- **Granularidade**: 1 linha = 1 conta em uma plataforma.
- **PK**: `id` (INT AUTO_INCREMENT)
- **FKs**: `client_id` -> `clients(id)`, `platform_id` -> `platforms(id)`.
- **Colunas**: `client_id` (INT NOT NULL), `platform_id` (INT NOT NULL), `external_account_id` (VARCHAR(100) NOT NULL), `name` (VARCHAR(150)), `currency` (CHAR(3) DEFAULT 'BRL'), `timezone` (VARCHAR(50) DEFAULT 'America/Sao_Paulo'), `status` (ENUM('active','inactive') NOT NULL DEFAULT 'active'), `created_at`, `updated_at`.
- **Unique**: `uq_account_platform (platform_id, external_account_id)`.

#### Tabela: `campaigns`
- **Propósito**: Campanhas de mídia paga.
- **PK**: `id` (INT AUTO_INCREMENT)
- **FKs**: `ad_account_id` -> `ad_accounts(id)`.
- **Colunas**: `ad_account_id` (INT NOT NULL), `external_campaign_id` (VARCHAR(100) NOT NULL), `name` (VARCHAR(255) NOT NULL), `channel_type` (VARCHAR(50)), `objective` (VARCHAR(100)), `status` (VARCHAR(50) NOT NULL), `budget_type` (ENUM('daily','lifetime')), `budget_amount` (DECIMAL(14,2)), `start_date` (DATE), `end_date` (DATE), `created_at`, `updated_at`.
- **Unique**: `uq_campaign_account (ad_account_id, external_campaign_id)`.

#### Tabela: `ad_groups`
- **Propósito**: Grupos de anúncios (Google) / Conjuntos de anúncios (Meta).
- **PK**: `id` (INT AUTO_INCREMENT)
- **FKs**: `campaign_id` -> `campaigns(id)`.
- **Colunas**: `campaign_id` (INT NOT NULL), `external_ad_group_id` (VARCHAR(100) NOT NULL), `name` (VARCHAR(255) NOT NULL), `status` (VARCHAR(50) NOT NULL), `targeting_summary` (TEXT), `created_at`, `updated_at`.
- **Unique**: `uq_adgroup_campaign (campaign_id, external_ad_group_id)`.

#### Tabela: `ads`
- **Propósito**: Criativos e peças individuais.
- **PK**: `id` (INT AUTO_INCREMENT)
- **FKs**: `ad_group_id` -> `ad_groups(id)`.
- **Colunas**: `ad_group_id` (INT NOT NULL), `external_ad_id` (VARCHAR(100) NOT NULL), `name` (VARCHAR(255)), `format` (VARCHAR(50)), `headline` (VARCHAR(255)), `description` (TEXT), `creative_url` (VARCHAR(500)), `status` (VARCHAR(50) NOT NULL), `created_at`, `updated_at`.
- **Unique**: `uq_ad_adgroup (ad_group_id, external_ad_id)`.

---

### 23.2. Tabelas Fato de Métricas (Segregadas por Granularidade)

#### Tabela: `fact_campaign_daily_metrics`
- **Propósito**: Armazenar métricas diárias consolidadas no nível de campanha (Fato Mestre de Performance).
- **Granularidade**: `campaign_id + metric_date`.
- **PK**: `id` (BIGINT AUTO_INCREMENT)
- **FKs**: `campaign_id` -> `campaigns(id)`.
- **Colunas**:
  - `campaign_id` (INT NOT NULL)
  - `metric_date` (DATE NOT NULL)
  - `impressions` (BIGINT NOT NULL DEFAULT 0)
  - `clicks` (BIGINT NOT NULL DEFAULT 0)
  - `cost_micros` (BIGINT NOT NULL DEFAULT 0) — *Custo exato na moeda da conta sem perda de precisão*
  - `spend` (DECIMAL(14,2) AS (cost_micros / 1000000.0) STORED) — *Coluna gerada para facilidade de consulta*
  - `conversions` (DECIMAL(12,2) NOT NULL DEFAULT 0)
  - `conversions_value` (DECIMAL(14,2) NOT NULL DEFAULT 0)
  - `all_conversions` (DECIMAL(12,2) NOT NULL DEFAULT 0)
  - `all_conversions_value` (DECIMAL(14,2) NOT NULL DEFAULT 0)
  - `video_views` (BIGINT DEFAULT 0)
  - `created_at` (DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP)
- **Unique**: `uq_fact_camp_date (campaign_id, metric_date)`
- **Índice**: `idx_camp_metrics_date (metric_date, campaign_id)`

#### Tabela: `fact_campaign_device_metrics`
- **Propósito**: Métricas de campanha segmentadas por tipo de dispositivo.
- **Granularidade**: `campaign_id + metric_date + device`.
- **PK**: `id` (BIGINT AUTO_INCREMENT)
- **FKs**: `campaign_id` -> `campaigns(id)`.
- **Colunas**:
  - `campaign_id` (INT NOT NULL)
  - `metric_date` (DATE NOT NULL)
  - `device` (VARCHAR(30) NOT NULL) — *ex: MOBILE, DESKTOP, TABLET, OTHER*
  - `impressions` (BIGINT NOT NULL DEFAULT 0)
  - `clicks` (BIGINT NOT NULL DEFAULT 0)
  - `cost_micros` (BIGINT NOT NULL DEFAULT 0)
  - `conversions` (DECIMAL(12,2) NOT NULL DEFAULT 0)
  - `created_at` (DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP)
- **Unique**: `uq_fact_camp_device_date (campaign_id, metric_date, device)`

#### Tabela: `fact_campaign_conversion_actions`
- **Propósito**: Detalhamento de cada ação de conversão reportada na campanha.
- **Granularidade**: `campaign_id + metric_date + conversion_action_name`.
- **PK**: `id` (BIGINT AUTO_INCREMENT)
- **FKs**: `campaign_id` -> `campaigns(id)`.
- **Colunas**:
  - `campaign_id` (INT NOT NULL)
  - `metric_date` (DATE NOT NULL)
  - `conversion_action_name` (VARCHAR(150) NOT NULL) — *ex: Compra, Lead WhatsApp, Visualização*
  - `conversions` (DECIMAL(12,2) NOT NULL DEFAULT 0)
  - `conversions_value` (DECIMAL(14,2) NOT NULL DEFAULT 0)
  - `all_conversions` (DECIMAL(12,2) NOT NULL DEFAULT 0)
  - `all_conversions_value` (DECIMAL(14,2) NOT NULL DEFAULT 0)
  - `created_at` (DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP)
- **Unique**: `uq_fact_camp_conv_action (campaign_id, metric_date, conversion_action_name)`

#### Tabela: `fact_ad_daily_metrics`
- **Propósito**: Métricas diárias de criativos e anúncios individuais.
- **Granularidade**: `ad_id + metric_date`.
- **PK**: `id` (BIGINT AUTO_INCREMENT)
- **FKs**: `ad_id` -> `ads(id)`.
- **Colunas**:
  - `ad_id` (INT NOT NULL)
  - `metric_date` (DATE NOT NULL)
  - `impressions` (BIGINT NOT NULL DEFAULT 0)
  - `clicks` (BIGINT NOT NULL DEFAULT 0)
  - `cost_micros` (BIGINT NOT NULL DEFAULT 0)
  - `conversions` (DECIMAL(12,2) NOT NULL DEFAULT 0)
  - `created_at` (DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP)
- **Unique**: `uq_fact_ad_date (ad_id, metric_date)`

#### Tabela: `sync_logs`
- **Propósito**: Observabilidade e controle de execuções de sincronização.
- **PK**: `id` (BIGINT AUTO_INCREMENT)
- **Colunas**:
  - `ad_account_id` (INT NOT NULL)
  - `start_date` (DATE NOT NULL)
  - `end_date` (DATE NOT NULL)
  - `status` (ENUM('running','success','failed') NOT NULL)
  - `records_ingested` (INT DEFAULT 0)
  - `duration_seconds` (DECIMAL(8,2))
  - `error_message` (TEXT)
  - `created_at` (DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP)

---

## 24. ERD Textual Proposto

```text
[ organizations ]
       │ 1
       │
       └──< 0..N [ clients ] ◄─── (slug = pasta no Vault)
                     │ 1
                     │
                     └──< 1..N [ ad_accounts ] >──1 [ platforms ]
                                   │ 1
                                   │
                                   └──< 1..N [ campaigns ]
                                                 │ 1
       ┌─────────────────────────────────────────┼────────────────────────────────────────┐
       │ 1                                       │ 1                                      │ 1
       ▼ N                                       ▼ N                                      ▼ N
[ fact_campaign_daily_metrics ]     [ fact_campaign_device_metrics ]     [ fact_campaign_conversion_actions ]
       │
       └──< 1..N [ ad_groups ]
                     │ 1
                     └──< 1..N [ ads ]
                                   │ 1
                                   └──< 1..N [ fact_ad_daily_metrics ]
```

---

## 25. Estratégia de Sincronização

1. **Backfill Inicial (Histórico)**:
   - Execução única por conta buscando dados desde o início do ano anterior (ex: `2025-01-01` até `2026-08-01`).
   - Paginação em blocos mensais via `search_stream` do Google Ads para evitar estouro de memória.
2. **Sincronização Incremental (Diária)**:
   - Job diário executando na madrugada.
   - Período: janela móvel de `D-7` até `D-1` (permite atualizar conversões tardias e ajustes de faturamento).
   - Operação de persistência usando `INSERT ... ON DUPLICATE KEY UPDATE` garantindo idempotência absoluta.
3. **Tratamento de Rate Limits e Erros**:
   - Tratamento de exceções `GoogleAdsException` com *exponential backoff* em caso de erro `RESOURCE_EXHAUSTED`.
   - Gravação de status e log de erro em `sync_logs`.

---

## 26. Decisão: Recriar ou Evoluir o Banco

```text
================================================================================
RECOMENDAÇÃO TÉCNICA: RECRIAR O BANCO DO ZERO
================================================================================
```

### Justificativas Técnicas:
1. **Ambiente Laboratorial**: O projeto não possui dados de clientes reais em produção. Não há risco de perda de dados.
2. **Incompatibilidade Fundamental do Grão**: O schema atual obriga `ad_id` em todas as métricas, impedindo a ingestão direta de relatórios de campanha e segmentações do Google Ads.
3. **Limpeza de Tabelas Prematuras**: Remove as tabelas de CRM (`leads`, `landing_pages`, `conversions`) que estavam poluindo o modelo antes do pipeline de mídia estar consolidado.
4. **Alinhamento com o Vault**: Permite cadastrar imediatamente os 5 clientes reais do Vault (`hospital-de-olhos-videira`, `cardoso-empreendimentos`, etc.) com seus slugs corretos.
5. **Custo-Benefício**: Criar migrations para alterar tabelas existentes seria muito mais complexo e frágil do que aplicar um novo `0001_initial_schema.sql` limpo e dimensionado corretamente.

---

## 27. Roadmap de Execução

```text
FASE 1 — Recriação do Schema e Alinhamento com o Vault
   ├── Criar novo 0001_initial_schema.sql com o modelo de fatos segregados
   └── Popular clients com os 5 clientes reais do Vault

FASE 2 — Pipeline de Ingestão Google Ads
   ├── Construir ingestor automatizado que consome GoogleAdsService
   └── Persistir dados em fact_campaign_daily_metrics e fatos segmentados

FASE 3 — Atualização das Ferramentas da IA (src/ai_tools/)
   ├── Refatorar get_campaign_performance.py (corrigir joins e remoção do SUM(reach))
   ├── Criar get_campaign_comparison.py (suporte a comparações YoY e MoM)
   └── Atualizar AI_GUIDE.md com o novo catálogo

FASE 4 — Validação da Meta Ads API
   ├── Testar chamadas via Postman / Graph API assim que o acesso for liberado
   └── Criar o módulo src/integrations/meta_ads/ e seu pipeline de ingestão

FASE 5 — Camada Analítica e Relatórios Automatizados
   └── Construir ferramentas de geração de relatórios de fechamento de mês e alertas de anomalia
```

---

## 28. Próximos Experimentos Recomendados

1. **Experimento 1 (Google Ads Pipeline)**: Criar script `sync_google_ads.py` para sincronizar os dados reais da conta `4378571170` diretamente para as novas tabelas de fatos e validar a consistência com o painel do Google Ads.
2. **Experimento 2 (Comparação Histórica na IA)**: Executar uma consulta via IA comparando 30 dias de performance entre duas campanhas reais do cliente para validar a acurácia dos cálculos de CPC, CTR e conversões.
3. **Experimento 3 (Meta Ads Sandbox)**: Realizar requisição na Graph API (`act_<ACCOUNT_ID>/insights`) para capturar o payload bruto e mapear os nomes das ações de conversão da Meta.

---

## 29. Respostas Obrigatórias às 22 Perguntas

1. **Qual é o verdadeiro domínio do Sync?**  
   É uma plataforma analítica multi-plataforma de marketing para agências, que une métricas estruturadas de mídia paga a contextos estratégicos em Markdown para diagnóstico de performance e habilitação de IA.
2. **O que é Organization?**  
   A entidade de topo que representa uma holding ou grupo empresarial proprietário de uma ou mais marcas/empresas.
3. **O que é Client/Brand?**  
   A marca ou empresa específica atendida pela agência, cujo `slug` mapeia diretamente para sua pasta de conhecimento no Vault.
4. **O que é Ad Account?**  
   A conta de anúncios em uma plataforma específica (ex: Google Ads Customer ID ou Meta Ad Account) vinculada a uma marca.
5. **Como uma organização possui múltiplas marcas?**  
   Através do relacionamento 1:N entre `organizations` e `clients` (`clients.organization_id = organizations.id`).
6. **Como uma marca possui múltiplas contas?**  
   Através do relacionamento 1:N entre `clients` e `ad_accounts` (uma marca pode ter 1 conta Google Ads, 2 contas Meta Ads, etc.).
7. **Quais entidades são comuns entre plataformas?**  
   Organization, Client, Ad Account, Campaign, Ad Group/Ad Set, Ad, e as métricas brutas (impressões, cliques, custo, conversões).
8. **Quais são específicas?**  
   Nomes e IDs de ações de conversão, tipos de canais específicos (ex: Performance Max no Google vs Advantage+ na Meta), segmentações geográficas e IDs de critérios.
9. **Qual é o grain de cada fato?**  
   - `fact_campaign_daily_metrics`: `campaign_id + metric_date`
   - `fact_campaign_device_metrics`: `campaign_id + metric_date + device`
   - `fact_campaign_conversion_actions`: `campaign_id + metric_date + conversion_action_name`
   - `fact_ad_daily_metrics`: `ad_id + metric_date`
10. **Como evitar duplicação?**  
    Definindo `UNIQUE KEY` composta sobre o grão exato de cada tabela fato e utilizando `INSERT ... ON DUPLICATE KEY UPDATE` em todas as ingestões.
11. **Como guardar histórico?**  
    Através de fatos imutáveis persistidos no banco local indexados por data e campanha, permitindo consultas instantâneas sem bater nas APIs externas.
12. **Como sincronizar campanhas ativas?**  
    Com um job diário que sincroniza uma janela móvel retroativa (últimos 7 dias) para capturar ajustes de conversão tardia.
13. **Como armazenar campanhas encerradas?**  
    Após o fechamento da janela de atribuição, os dados tornam-se snapshots históricos imutáveis no banco de dados.
14. **Como representar conversões?**  
    No nível agregado de campanha em `fact_campaign_conversion_actions`, onde cada linha armazena a métrica de uma ação específica (`WhatsApp`, `Compra`, `Formulário`).
15. **Como representar dispositivos?**  
    Através da tabela fato dedicada `fact_campaign_device_metrics` com o enum/string do dispositivo (`MOBILE`, `DESKTOP`, `TABLET`).
16. **Como representar geografia?**  
    Através de tabela fato `fact_campaign_geo_metrics` contendo `geo_target_id` associada à campanha e data (quando a query geográfica for ativada no pipeline).
17. **Como comparar períodos?**  
    Consultando a tabela `fact_campaign_daily_metrics` filtrando os dois intervalos de data (`BETWEEN`) e agrupando por campanha para comparar variações percentuais de métricas base e derivadas.
18. **O banco atual suporta isso?**  
    **Não.** O banco atual exige `ad_id` em todas as métricas e não possui suporte a segmentações por dispositivo ou ações de conversão separadas.
19. **O que precisa ser refeito?**  
    O schema do banco de dados (DDL), o arquivo de seeds (para alinhar com o Vault) e as queries analíticas das ferramentas Python em `src/ai_tools/`.
20. **Qual é o menor banco que sustenta corretamente o MVP?**  
    Um banco com 8 tabelas: `organizations`, `clients`, `platforms`, `ad_accounts`, `campaigns`, `ad_groups`, `ads`, e a tabela fato principal `fact_campaign_daily_metrics` (acrescida de `fact_campaign_conversion_actions` e `sync_logs`).
21. **O que NÃO devemos implementar ainda?**  
    Não implementar tabelas de CRM manual (`leads`, `landing_pages`), automações complexas de escrita em campanhas, integrações com LinkedIn/TikTok e abstrações prematuras de IA sem dados reais consolidados.
22. **Qual é o próximo experimento técnico de maior valor?**  
    Construir o script de ingestão real da API do Google Ads para persistir as métricas da conta `4378571170` na nova tabela `fact_campaign_daily_metrics` e validar a conciliação dos números contra o Google Ads Web UI.

---

## 30. Conclusão

O projeto **Sync** possui uma base conceitual e diretrizes de segurança extremamente sólidas (`AI_GUIDE.md` e regras de agente read-only são exemplares). O gargalo que impedia o avanço residia exclusivamente na **modelagem de dados relacional inicial**, que tentou unificar métricas em um nível de detalhe inadequado (`ad_id`).

Com a recriação do banco orientada ao modelo dimensional proposto neste documento e o alinhamento dos clientes com o Vault, o sistema estará 100% pronto para receber dados reais, habilitar análises de diagnóstico de causa-raiz e potencializar a camada de inteligência artificial com total confiabilidade técnica.
