# Sync — Documentação Técnica do Projeto

> Gerado a partir de análise completa do repositório em `C:\dev\sync` (branch `db_google_test`).
> Esta documentação reflete o **estado real do código no momento da análise**, incluindo divergências entre o schema de banco recém-recriado e o código que ainda o consome.

---

## 1. O que é o Sync

O Sync é um projeto pessoal em estágio de MVP para uma agência de publicidade/marketing. Ele integra três camadas:

```text
CONHECIMENTO (Vault/Markdown, Obsidian)  →  contexto estratégico de cada cliente
DADOS (MariaDB)                          →  métricas de mídia paga estruturadas
INTELIGÊNCIA (Agente de IA)              →  responde perguntas cruzando as duas fontes
```

Objetivo de negócio: permitir que um agente de IA responda perguntas como "por que a campanha X performou pior que no mesmo período do ano passado?" combinando números do banco com o contexto registrado nas reuniões/briefings dos clientes reais da agência.

O projeto está em ambiente de laboratório: sem dados de produção, com dados fictícios (`seed_safe.sql`) e 5 clientes reais documentados apenas no Vault (ainda não replicados no banco).

---

## 2. Stack Tecnológica

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.13 (Windows, `.venv` local) |
| Banco | MariaDB/MySQL (`sync_db`, `localhost:3306`) |
| Driver DB | `PyMySQL` 1.2.0 (`DictCursor`) |
| Config | `python-dotenv` 1.2.2 |
| Ads API | `google-ads` (SDK oficial, gRPC/Protobuf), `google-auth`, `google-auth-oauthlib`, `requests-oauthlib` |
| Conhecimento | Markdown + Obsidian (`vault/Sync/`) |
| Controle de versão | Git |

**Observação:** `requirements.txt` só lista `PyMySQL==1.2.0` e `python-dotenv==1.2.2`. As dependências do Google Ads (`google-ads`, `google-auth*`, `requests-oauthlib`) estão instaladas no `.venv` mas **não estão declaradas** no arquivo — reinstalar o ambiente do zero (`pip install -r requirements.txt`) quebraria `src/integrations/google_ads/*`. O próprio arquivo também está salvo com encoding estranho (aparenta UTF-16/BOM, o `Read` retornou bytes de BOM antes do texto).

---

## 3. Estrutura de Diretórios (estado atual)

```text
sync/
├── .agents/rules/sync-ai-safety.md     # Regra de segurança persistente (Antigravity)
├── .env.admin                          # Credenciais admin + Google Ads (gitignored)
├── .env.agent                          # Credenciais read-only da IA (gitignored)
├── .env.example                        # Template das duas seções de env vars
├── AI_GUIDE.md                         # Guia operacional/segurança do agente de IA (raiz, leitura obrigatória)
├── auditoria_tecnica_e_dominio_sync.md # Auditoria anterior (ver §11 — parcialmente desatualizada)
├── requirements.txt                    # Incompleto (ver §2)
├── schema.sql                          # Schema ANTIGO na raiz — DESATUALIZADO, não reflete o banco atual (ver §5)
├── seed_safe.sql                       # Seed fictício — hoje INCOMPATÍVEL com o schema atual (ver §6.4)
├── tree.md                             # Árvore de arquivos gerada manualmente (inclui .venv)
├── src/
│   ├── ai_tools/            # Ferramentas READ_ONLY autorizadas para o agente de IA
│   │   ├── db.py                          # Conexão via .env.agent (usuário sync_ai)
│   │   ├── get_client_info.py             # VALIDADO
│   │   ├── get_client_campaigns.py        # QUEBRADO contra o schema atual (ver §6.4)
│   │   ├── get_campaign_performance.py    # QUEBRADO/impreciso contra o schema atual (ver §6.4)
│   │   └── get_client_conversions.py      # QUEBRADO — tabela `conversions` não existe mais (ver §6.4)
│   ├── db/
│   │   ├── admin.py                       # Conexão admin via .env.admin (usuário sync_admin)
│   │   └── run_migrations.py              # Runner sequencial de migrations (modificado recentemente)
│   ├── integrations/
│   │   ├── google_ads/       # Integração validada (autenticação, campanhas, métricas, geo, hierarquia MCC)
│   │   └── meta_ads/          # Vazio — aguardando liberação de acesso ao Business Portfolio
│   ├── migrations/
│   │   ├── 0002_core_schema.sql           # Schema ATUAL (única migration executável pelo runner)
│   │   └── legacy/0001_initial_schema.sql # Schema antigo, mantido como checkpoint histórico (ignorado pelo runner)
│   ├── queries/clients.py                 # Arquivo vazio (código morto)
│   └── tests/
│       ├── test_connection.py             # Funcional
│       └── test_data/                     # 2 scripts com imports quebrados (`db.connection` não existe)
└── vault/Sync/clientes/       # 5 clientes reais da agência (Markdown/Obsidian)
    ├── bragagnolo-advocacia/
    ├── cantina-toscana/
    ├── cardoso-empreendimentos/
    ├── hospital-de-olhos-videira/
    └── vigor-studio/
```

---

## 4. Modelo de Segurança do Agente de IA

Este é o ponto mais maduro do projeto. Duas camadas reforçam o mesmo contrato:

- **`AI_GUIDE.md`** (raiz): guia operacional completo (36 seções) que qualquer agente de IA deve ler antes de qualquer ação no projeto.
- **`.agents/rules/sync-ai-safety.md`**: regra persistente de workspace que injeta a leitura do `AI_GUIDE.md` automaticamente.

Regras centrais:

1. **O agente nunca acessa o MariaDB diretamente.** Toda consulta de dados passa por um script Python explicitamente catalogado em `src/ai_tools/`.
2. **Segregação de usuários de banco:** `sync_admin` (DDL/DML, via `.env.admin`) vs `sync_ai` (somente `SELECT`, via `.env.agent`).
3. **Catálogo fechado de ferramentas** (seção 26 do `AI_GUIDE.md`): `get_client_info`, `get_client_campaigns`, `get_campaign_performance`, `get_client_conversions` — todas marcadas `READ_ONLY` e `VALIDADO`. Se não existe ferramenta para a pergunta, o agente deve **parar e informar**, nunca improvisar SQL.
4. **Sem SQL arbitrário, sem rede não autorizada, sem MCP não autorizado, sem alteração de dados nesta fase.**
5. **Credenciais nunca aparecem em respostas** — nem para confirmar que existem.
6. Toda ferramenta usa queries parametrizadas (`%s`), eliminando risco de SQL injection.

**Risco identificado:** o catálogo do `AI_GUIDE.md` ainda marca as 4 ferramentas como `VALIDADO`, mas 3 delas estão quebradas contra o schema atual (`0002_core_schema.sql`) — ver §6.4. O guia não foi atualizado após a recriação do banco, então hoje ele autoriza formalmente ferramentas que falhariam em runtime.

---

## 5. Banco de Dados — Estado Atual vs. Histórico

O `git status` revela que o banco **já está sendo recriado** desde a auditoria anterior: `src/migrations/0001_initial_schema.sql` foi movido para `src/migrations/legacy/`, e uma nova `src/migrations/0002_core_schema.sql` foi criada. Isso implementa (parcialmente) a recomendação "recriar o banco do zero" da auditoria anterior.

### 5.1 O que mudou de v1 (legacy) para v2 (atual)

| Aspecto | v1 (`legacy/0001`) | v2 (`0002_core_schema.sql`, atual) |
|---|---|---|
| Hierarquia | `clients` era o topo | **`organizations` → `clients`** (suporta holdings com múltiplas marcas) |
| Tipos de PK | `INT` | `BIGINT` (exceto `platforms`/`metric_dimensions`: `SMALLINT`) |
| Tabelas de CRM | `landing_pages`, `leads`, `conversions` | **Removidas** — MVP focado só em mídia |
| Segmentação de métricas | Nenhuma | Nova tabela `metric_dimensions` + coluna `daily_metrics.metric_dimension_id` (nullable) |
| Observabilidade de sync | Não existia | Nova tabela `data_sync_runs` (status de cada execução de ingestão) |
| `campaigns.budget_type` / `budget_amount` | Existiam | **Removidos** (substituídos por `campaign_type`) |
| `daily_metrics.spend` | `DECIMAL(12,2)` | `DECIMAL(18,6)` (mais precisão) |
| Granularidade de `daily_metrics` | Amarrada a `ad_id` | **Ainda amarrada a `ad_id`** — não resolve o problema de granularidade de campanha apontado na auditoria anterior |

### 5.2 Schema atual — tabelas (`0002_core_schema.sql`)

1. **`schema_migrations`** — controle de migrations aplicadas.
2. **`organizations`** — holding/grupo econômico (`id`, `name`, `slug` único, `status`).
3. **`clients`** — marca/cliente da agência. `organization_id` **NOT NULL** (FK `RESTRICT`), slug único **por organização** (`uq_clients_organization_slug`, não mais globalmente único como em v1).
4. **`platforms`** — lookup (Google Ads, Meta Ads, LinkedIn Ads, TikTok Ads), populada via `INSERT` na própria migration.
5. **`ad_accounts`** — conta de anúncio por cliente/plataforma.
6. **`campaigns`** — sem orçamento; tem `campaign_type` além de `objective`/`status`.
7. **`ad_groups`** — grupos/conjuntos de anúncio.
8. **`ads`** — anúncios individuais (`ad_type` no lugar de `format`/`headline`/`creative_url`).
9. **`metric_dimensions`** — dimensões de segmentação (`dimension_type` + `dimension_value`, ex.: `device`/`MOBILE`).
10. **`daily_metrics`** — chave única agora é `(ad_id, metric_date, metric_dimension_id)`, ou seja, **múltiplas linhas por ad+data são possíveis** (uma por dimensão, mais uma "linha total" com dimensão `NULL`, se o pipeline de ingestão optar por gravá-la).
11. **`data_sync_runs`** — log de execuções de sincronização (status `running/success/partial/failed`).

### 5.3 Problema estrutural que persiste

A crítica central da auditoria anterior — **métricas amarradas a `ad_id`, impossibilitando ingestão de relatórios no nível de campanha** — **não foi resolvida** na v2. O novo design generalizou a segmentação (via `metric_dimensions`) em vez de segregar por granularidade (fatos separados por campanha/dispositivo/ação de conversão, como a própria auditoria havia proposto no §23). Isso significa:

- Um relatório do Google Ads no grão `campaign + date` (sem quebra por anúncio) ainda não tem onde ser gravado.
- Segmentações que não pertencem ao anúncio isoladamente (geografia, ação de conversão) também não têm modelagem própria — teriam que ser forçadas dentro de `metric_dimensions`, o que mistura conceitos (device é uma dimensão do mesmo fato; conversion action é outro fato com métricas próprias).

### 5.4 Novo risco introduzido pela v2: duplicidade em agregações

Como a chave única de `daily_metrics` passou a incluir `metric_dimension_id`, uma mesma combinação `ad_id + metric_date` pode ter **múltiplas linhas** (uma por dispositivo, por exemplo) no momento em que o pipeline de ingestão por dispositivo for implementado. Qualquer query que faça `SUM(...)` sem filtrar `metric_dimension_id IS NULL` (ou sem agregar as dimensões antes) contará os mesmos cliques/impressões mais de uma vez. `get_campaign_performance.py` (ver §6.4) já tem esse padrão de `SUM` sem esse filtro — hoje inofensivo (não há dados segmentados), mas é uma bomba-relógio para o dia em que a ingestão por device for ligada.

### 5.5 `schema.sql` na raiz está obsoleto

O arquivo `schema.sql` na raiz do projeto ainda reflete o schema v1 (idêntico ao que hoje está em `legacy/0001`). Ele não foi atualizado nem removido após a criação do `0002_core_schema.sql`. Isso é uma fonte real de confusão: quem abrir `schema.sql` esperando ver o schema vigente verá uma versão desatualizada há uma migration inteira.

---

## 6. Camada Python de Acesso a Dados

### 6.1 `src/db/admin.py`
Conexão administrativa via `.env.admin` (usuário `sync_admin`, variáveis `DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD`). `autocommit=False` — quem chama é responsável por `commit()`. Usada por `run_migrations.py`.

### 6.2 `src/ai_tools/db.py`
Conexão restrita via `.env.agent` (usuário `sync_ai`, variáveis `SYNC_DB_*`). `autocommit=True`. Expõe apenas `fetch_one`/`fetch_all` parametrizados — nenhuma função de escrita existe nesse módulo, então mesmo um bug não permitiria `INSERT/UPDATE/DELETE` a partir dele.

### 6.3 `src/db/run_migrations.py`
Runner sequencial: lista `*.sql` em `src/migrations/` (não recursivo — por isso `legacy/` é ignorado automaticamente), separa cada arquivo por `;` e executa instrução por instrução, registrando o nome do arquivo em `schema_migrations` ao final.

**Mudança recente (`git diff` não commitado):** foi adicionada uma checagem via `information_schema.tables` que detecta se `schema_migrations` ainda não existe e, nesse caso, trata como "nenhuma migration aplicada" em vez de lançar exceção. Isso é exatamente o que permite rodar `0002_core_schema.sql` (que cria a própria tabela `schema_migrations`) em um banco totalmente vazio — correção necessária e coerente com a recriação do banco.

**Limitação conhecida (herdada, não corrigida):** o split ingênuo por `;` quebra se qualquer statement futuro contiver `;` dentro de uma string, trigger ou stored procedure. Para SQL simples como o atual, funciona; não é robusto para o futuro.

### 6.4 Ferramentas de IA (`src/ai_tools/`) — auditoria de compatibilidade com o schema v2

Esta é a descoberta mais importante desta análise: **as 4 ferramentas catalogadas como `VALIDADO` no `AI_GUIDE.md` foram escritas contra o schema v1 e não foram atualizadas após a migration `0002`.**

| Ferramenta | Status real contra `0002_core_schema.sql` | Motivo |
|---|---|---|
| `get_client_info.py` | **OK** | Só usa `id, name, slug, industry, status, created_at, updated_at` de `clients` — todas ainda existem em v2. |
| `get_client_campaigns.py` | **QUEBRADO** | Faz `SELECT campaigns.budget_type, campaigns.budget_amount` — essas colunas **foram removidas** em `0002_core_schema.sql`. A query falhará com "Unknown column" no MariaDB. |
| `get_campaign_performance.py` | **QUEBRADO + impreciso** | (a) Mesma classe de erro não ocorre aqui pois não referencia `budget_*`, mas (b) `COALESCE(SUM(daily_metrics.reach), 0)` continua somando `reach` ao longo dos dias — matematicamente inválido (alcance não é aditivo, é uma métrica de únicos); (c) `INNER JOIN daily_metrics` faz a campanha inteira sumir do resultado (`result is None` → erro 3) se nenhum anúncio tiver métrica no período, quando o correto seria `LEFT JOIN` retornando zeros; (d) vulnerável à duplicidade descrita em §5.4 assim que existirem linhas segmentadas por `metric_dimension_id`. |
| `get_client_conversions.py` | **QUEBRADO** | Depende inteiramente da tabela `conversions`, que **foi removida** em `0002_core_schema.sql`. Toda execução falhará com "Table 'sync_db.conversions' doesn't exist". |

**Consequência prática:** hoje, 3 das 4 únicas ferramentas que o agente de IA tem autorização para usar não funcionam contra o banco atual. Isso não é um problema de segurança (as falhas são erros de SQL capturados pelo `try/except` de cada script, retornando `{"ok": false, "error": ...}` — nada quebra silenciosamente nem expõe dado indevido), mas é um bloqueador funcional: o agente, seguindo o `AI_GUIDE.md` à risca, tentará usar ferramentas "validadas" que não retornam dados reais.

### 6.5 `src/queries/clients.py`
Arquivo vazio — resquício de uma estrutura abandonada (`db.queries.clients`), referenciado pelos scripts de teste quebrados abaixo.

### 6.6 Testes (`src/tests/`)
- `test_connection.py`: funcional, testa `SELECT 1` via `src.ai_tools.db.get_connection` (usuário `sync_ai`).
- `test_data/seed_test_data.py` e `test_data/query_test_data.py`: código morto — importam `db.connection` e `db.queries.clients`, módulos que nunca existiram na estrutura atual (`src/db/`, `src/queries/`). Falham imediatamente com `ModuleNotFoundError`.
- Não há testes automatizados (`pytest` ou similar) para as ferramentas de IA — os bugs do §6.4 não seriam pegos por CI hoje porque não existe CI/test suite real, só scripts manuais.

---

## 7. Integrações Externas

### 7.1 Google Ads — validado e funcional
- Autenticação OAuth2 (`InstalledAppFlow`) com `refresh_token` offline persistido em `.env.admin`.
- MCC (conta gerente): `GOOGLE_ADS_LOGIN_CUSTOMER_ID`. Conta operacional: `GOOGLE_ADS_CUSTOMER_ID`.
- `src/integrations/google_ads/client.py`: monta o `GoogleAdsClient` e traz uma consulta validada em `geographic_view` (nota no código: misturar campos de `ad_group_ad` no `FROM geographic_view` quebra a API — lição aprendida documentada implicitamente no isolamento da query).
- `src/integrations/google_ads/metrics.py`: `get_daily_campaign_metrics()` consulta `campaign + segments.date` com `impressions, clicks, cost_micros, conversions, ctr, average_cpc, cost_per_conversion`, convertendo micros para valor monetário dividindo por `1_000_000`. **Retorna uma lista de dicts em Python — não persiste no banco.** Não há nenhum pipeline de ingestão real ainda; todos os scripts em `google_ads/` são exploratórios/de teste (`test_campaigns.py`, `test_connection.py`, `test_hierarchy.py`, `test_metrics.py`), sem `INSERT ... ON DUPLICATE KEY UPDATE` em lugar nenhum do repositório.
- `generate_refresh_token.py`: script local de setup OAuth (fluxo interativo, não roda como parte de nenhum pipeline).

### 7.2 Meta Ads — não iniciado
`src/integrations/meta_ads/` está vazio. Bloqueio operacional (fora do código): verificação de dispositivo pendente no Meta for Developers e liberação de permissões no Business Portfolio da agência.

### 7.3 LinkedIn Ads / TikTok Ads
Existem apenas como linhas de lookup na tabela `platforms`. Nenhum código de integração.

---

## 8. Vault (Base de Conhecimento)

`vault/Sync/clientes/` é um vault Obsidian com 5 clientes reais da agência, cada um com a mesma estrutura de arquivos:

```text
<cliente>/
├── cliente.md                  # frontmatter YAML + identidade, objetivo de negócio, resumo executivo
├── equipe-*.md                 # equipe (nome varia: socios, cozinha, comercial, medica, professores)
├── estilo-visual.md
├── gatilhos-mentais.md
├── posicionamento-e-marca.md
├── produtos.md
├── tom-de-voz.md
├── canais/instagram.md
├── publico-alvo/persona-*.md   # 2–3 personas por cliente
└── reunioes/DD-MM-2026.md      # atas de reunião datadas
```

Clientes documentados: `bragagnolo-advocacia` (jurídico/OAB), `cantina-toscana` (restaurante), `cardoso-empreendimentos` (imobiliário), `hospital-de-olhos-videira` (saúde/oftalmologia — o mais detalhado, com 4 atas de reunião), `vigor-studio` (fitness).

Cada `cliente.md` usa frontmatter estruturado (`tipo`, `nome`, `segmento`, `status`, `tags`) e linka os demais arquivos via wikilinks `[[...]]`, seguindo convenções nativas do Obsidian. **Nenhum desses slugs (`hospital-de-olhos-videira`, etc.) existe hoje na tabela `clients` do banco** — o banco só tem os 5 clientes fictícios de `seed_safe.sql` (`seed-alpha-imoveis` etc.), que não têm nenhuma correlação com os clientes reais do Vault. Essa desconexão (já apontada na auditoria anterior) continua sem solução.

---

## 9. Segurança e Configuração

- **Segregação de credenciais em dois arquivos** (`.gitignore`d): `.env.admin` (DDL/DML + segredos do Google Ads) e `.env.agent` (somente `SELECT`, sem nenhum segredo de API externa).
- **`.env.example`** documenta as duas seções sem valores reais — serve de contrato para quem for configurar o ambiente.
- Não há `.env.local`/segredos versionados no Git (confirmado pelo `.gitignore` e pela ausência desses arquivos no `git status`).
- Todas as queries de `src/ai_tools/` e `src/db/` usam parâmetros (`%s`), sem concatenação de string — sem superfície de SQL injection nos caminhos auditados.
- `src/integrations/google_ads/metrics.py` monta a query do Google Ads com f-string interpolando datas (`start_date.isoformat()`), mas isso é GAQL (Google Ads Query Language) contra a API do Google, não SQL contra o MariaDB — risco de injeção é teoricamente presente se `start_date`/`end_date` viessem de input não controlado, mas hoje só são chamadas com objetos `date` já validados pelo tipo, não strings livres.

---

## 10. Débito Técnico — Resumo Consolidado

### Crítico (bloqueia uso real do agente de IA)
1. `get_client_campaigns.py` referencia colunas removidas (`budget_type`, `budget_amount`) → falha em runtime.
2. `get_client_conversions.py` depende de tabela removida (`conversions`) → falha em runtime.
3. `seed_safe.sql` é incompatível com `0002_core_schema.sql`: insere direto em `clients(id, name, slug, industry, status)` sem `organization_id` (agora `NOT NULL`), insere em `campaigns` com `budget_type`/`budget_amount` (colunas inexistentes), e depende de `landing_pages`/`leads`/`conversions` (tabelas removidas). **O seed não roda mais como está.**
4. Não existem clientes nem organizações reais cadastrados no banco atual — nenhuma ferramenta de IA tem dado real para consultar hoje.
5. `AI_GUIDE.md` continua declarando as 4 ferramentas como `VALIDADO`, dando ao agente uma falsa garantia de que elas funcionam.

### Alto
6. `daily_metrics` continua amarrada a `ad_id`; sem suporte a métricas no grão de campanha, ação de conversão ou geografia.
7. Risco de dupla contagem em agregações (`SUM`) assim que a segmentação por `metric_dimension_id` começar a ser preenchida (ver §5.4).
8. `SUM(daily_metrics.reach)` em `get_campaign_performance.py` continua matematicamente inválido.
9. `INNER JOIN` em vez de `LEFT JOIN` em `get_campaign_performance.py` faz campanhas sem métricas no período desaparecerem do resultado.
10. Nenhum pipeline de ingestão real (Google Ads só imprime/retorna em memória; nada persiste no banco).
11. `schema.sql` na raiz está desatualizado frente a `0002_core_schema.sql` — fonte de confusão para quem consultar o arquivo errado.
12. `requirements.txt` não lista as dependências do Google Ads de fato usadas no `.venv`.

### Médio
13. `src/tests/test_data/*.py` — imports quebrados, código morto.
14. `src/queries/clients.py` — arquivo vazio, código morto.
15. Split ingênuo por `;` em `run_migrations.py` (frágil para SQL mais complexo no futuro).
16. `tree.md` foi gerado incluindo a árvore completa do `.venv` (milhares de linhas irrelevantes) — deveria ser regenerado ignorando `.venv`.

---

## 11. Em relação à auditoria anterior (`auditoria_tecnica_e_dominio_sync.md`)

Esse documento — presente no repositório como arquivo não versionado — já havia feito um diagnóstico correto do schema v1 e recomendado explicitamente "recriar o banco do zero" com um modelo de fatos segregados por granularidade (`fact_campaign_daily_metrics`, `fact_campaign_device_metrics`, `fact_campaign_conversion_actions`, `fact_ad_daily_metrics`) mais `organizations`.

O que de fato aconteceu em `0002_core_schema.sql` foi uma recriação **parcial**:
- ✅ Implementado: `organizations` → `clients`, remoção das tabelas de CRM, tabela de observabilidade de sync (`data_sync_runs` ~ `sync_logs` proposto).
- ❌ Não implementado: a segregação de fatos por granularidade. Em vez disso, optou-se por generalizar via `metric_dimensions`, o que resolve segmentação por dispositivo mas não resolve métricas no grão de campanha (sem anúncio) nem ações de conversão como fato próprio.
- ❌ Não implementado: atualização das ferramentas de IA e do `AI_GUIDE.md` para o novo schema — por isso elas quebraram (§6.4).
- ❌ Não implementado: alinhamento entre os clientes do Vault e os clientes do banco.

Ou seja: a auditoria anterior permanece majoritariamente válida como diagnóstico de arquitetura de dados, mas está desatualizada quanto ao **estado do schema em si** (ela documenta o schema v1 como se fosse o atual). Esta documentação deve ser tratada como a referência mais recente.

---

## 12. Recomendações Priorizadas

1. **Corrigir as 3 ferramentas de IA quebradas** (`get_client_campaigns`, `get_campaign_performance`, `get_client_conversions`) para o schema `0002`, ou marcá-las explicitamente como `EM_MANUTENÇÃO` no `AI_GUIDE.md` até serem corrigidas — para não dar ao agente uma falsa sensação de disponibilidade.
2. **Reescrever `seed_safe.sql`** contra `0002_core_schema.sql` (incluindo `organizations` e removendo referências às tabelas de CRM), ou substituí-lo por um seed que já cadastre os 5 clientes reais do Vault com os slugs corretos.
3. **Decidir e documentar a modelagem de granularidade de métricas** antes de escrever qualquer pipeline de ingestão real — hoje ainda não há onde gravar métricas de campanha sem anúncio.
4. **Apagar ou atualizar `schema.sql`** na raiz para não conviver com duas fontes de verdade sobre o schema.
5. **Congelar `requirements.txt`** com `pip freeze` (ou equivalente) para refletir o que o `.venv` realmente usa.
6. Só depois disso: construir o pipeline real de ingestão do Google Ads (persistência com `INSERT ... ON DUPLICATE KEY UPDATE`) e, quando liberado, iniciar a integração Meta Ads.
