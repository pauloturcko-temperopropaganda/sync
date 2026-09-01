# Exploração da Google Ads API — Sync

> Revalidação completa, feita do zero (sem presumir nada da auditoria anterior), em 2026-09-01, contra a conta real configurada em `.env.admin`. Script usado: exploração ad-hoc (não faz parte do pipeline do projeto), payloads brutos salvos em `docs/google-ads-api-exploracao/payloads/*.json`.

---

## 0. Achado mais importante: a conta configurada é de um cliente real, não um sandbox

`GOOGLE_ADS_CUSTOMER_ID=4378571170` **não é uma conta de teste** — é a conta real do Google Ads da **Guararapes Internacional** (fabricante de MDF/móveis), com `customer.test_account = false`. A MCC (`GOOGLE_ADS_LOGIN_CUSTOMER_ID=8934723647`) é a própria **Tempero Propaganda** (a agência).

Isso muda a leitura de tudo que segue: os dados abaixo são operação real de um cliente, não dado fictício. Todas as consultas feitas foram somente leitura (GAQL `SELECT`), nada foi alterado na conta.

### Hierarquia completa da MCC (17 contas)

| Conta | Status | Observação |
|---|---|---|
| **Guararapes Internacional** (`4378571170`) | **ENABLED** | Única conta ativa hoje |
| Be Health | CANCELED | — |
| **Clínica de Olhos Videira** (`5514296045`) | CANCELED | **Correlaciona com `hospital-de-olhos-videira` no Vault** — provavelmente o mesmo cliente, conta de Ads antiga/encerrada |
| Dona Lola Cafeteria | CANCELED | — |
| Dr. Flávio Burg | CANCELED | — |
| Herdina & Langaro | CANCELED | — |
| Ice Paletas / Ice Paletas (2) | CANCELED | — |
| Infopasa | CANCELED | — |
| Pioneiro Baterias | CANCELED | — |
| Pladisa Itajaí | CANCELED | — |
| Tempero Propaganda | CANCELED | Conta própria da agência, sem uso |
| Unimed Videira | CANCELED | — |
| Conta Testes | CLOSED | — |
| Ecológica | CLOSED | — |
| PCN Papel e Embalagem | CLOSED | — |

**Implicação prática:** nenhuma das 16 contas restantes está acessível para consulta de métricas (todas `CANCELED`/`CLOSED` — a API ainda lista a hierarquia mas não retorna dado operacional relevante). Nenhuma delas corresponde diretamente aos outros 4 clientes do Vault (`bragagnolo-advocacia`, `cantina-toscana`, `cardoso-empreendimentos`, `vigor-studio`) — ou eles nunca tiveram Google Ads pela MCC, ou a conta está em outro lugar. A correlação com `hospital-de-olhos-videira` é a única batida clara, e mesmo essa está `CANCELED`.

Payload bruto: `payloads/01_hierarchy.json`, `payloads/02_customer.json`.

---

## 1. Autenticação — o que já foi resolvido nesta sessão

- Causa da falha anterior confirmada: refresh token expirado (app OAuth em modo *Testing* no Google Cloud → tokens expiram em 7 dias). Token regenerado pelo usuário via `generate_refresh_token.py`, funcionando.
- **Ainda pendente** (não resolvido, decisão do usuário foi adiar): publicar o app OAuth pra "In production" no Cloud Console, pra parar de expirar a cada 7 dias. Enquanto isso não for feito, qualquer pipeline automatizado (sync diário) vai quebrar sozinho em uma semana.

---

## 2. Bug de GAQL encontrado e corrigido durante a exploração

A consulta original de campanhas (meu primeiro rascunho, espelhando o padrão dos scripts já existentes no repo) incluía `campaign.start_date` e `campaign.end_date`:

```
Unrecognized fields in the query: 'campaign.start_date', 'campaign.end_date'.
```

Esses dois campos **não existem** no schema GAQL da versão em uso (`v25`, vinda do `google-ads` SDK instalado). Removidos, a query passou a funcionar (36 campanhas retornadas). **Nenhum código do repositório usa esses campos hoje** (nem `metrics.py`, nem `test_campaigns.py`), então não há nada quebrado em produção — mas é um lembrete de que qualquer GAQL novo precisa ser testado contra a versão real do SDK antes de assumir que um campo existe.

---

## 3. Campanhas (36 no total, só 1 ativa)

| Métrica | Valor |
|---|---|
| Total de campanhas | 36 |
| `ENABLED` | **1** |
| `REMOVED` | 35 |

A única campanha ativa: `22682629376` — **"[Av] YT Inscritos [International]"**, tipo `DEMAND_GEN` (Demand Gen — formato relativamente recente do Google, focado em YouTube/Discover), orçamento diário de `33.000.000` micros (R$ 33,00/dia), estratégia `MAXIMIZE_CONVERSIONS`. É a mesma campanha que já estava hardcoded em `src/integrations/google_ads/client.py` (`campaign.id = 22682629376`) — confirmado que esse ID não era arbitrário, é a única campanha realmente ativa da conta.

Diversidade real de `advertising_channel_type` encontrada nas 36 campanhas (histórico, mesmo que hoje removidas): `SMART`, `VIDEO`, `SEARCH`, `DISPLAY`, `PERFORMANCE_MAX`, `DEMAND_GEN`. Isso é relevante pra modelagem: o schema precisa acomodar pelo menos essas 6 famílias de campanha, cada uma com `advertising_channel_sub_type` próprio (`SMART_CAMPAIGN`, `VIDEO_SEQUENCE`, `UNSPECIFIED`, etc.).

Campo `campaign_budget.amount_micros` é `BIGINT`-scale (inteiro em milionésimos da moeda) — confirma que o schema atual (`0002_core_schema.sql`) não tem coluna de orçamento nenhuma (foi removida na recriação); se orçamento for necessário no relatório, precisa voltar, em `micros` (não `DECIMAL(12,2)` direto, pra não perder precisão — mesmo raciocínio já usado em `daily_metrics.spend`).

Payload bruto: `payloads/03_campaigns.json`.

---

## 4. Ad Groups e Ads

20 ad groups, 26 ads retornados (contas com histórico de ~5 anos de campanhas).

**Achado relevante pra modelagem:** o campo `ad_group_ad.ad.name` vem **vazio (`""`) para vários tipos de anúncio** (ex.: `SMART_CAMPAIGN_AD`). O "nome" do anúncio, quando existe, está em estruturas aninhadas específicas do tipo — só `RESPONSIVE_SEARCH_AD` retornou headlines/descriptions no formato esperado (`responsive_search_ad.headlines[].text`). Isso invalida a suposição do schema antigo (e do `0002_core_schema.sql` atual) de que `ads.name` é sempre um identificador útil — na prática, o "conteúdo" do anúncio depende do tipo e não cabe num único campo genérico.

Tipos de anúncio (`ad_group_ad.ad.type`) encontrados na conta real: `SMART_CAMPAIGN_AD`, `RESPONSIVE_SEARCH_AD`, `VIDEO_TRUEVIEW_IN_STREAM_AD`, `RESPONSIVE_DISPLAY_AD`, `IN_FEED_VIDEO_AD`, `EXPANDED_DYNAMIC_SEARCH_AD`, `DEMAND_GEN_VIDEO_RESPONSIVE_AD` — **7 tipos reais**, bem mais granular que o `format` livre (`image/video/carousel/search/responsive`) do schema legado (`legacy/0001`). O schema atual (`0002`) usa `ad_type VARCHAR(150)` livre, o que já comporta esses valores sem problema — só registrar que são esses os valores reais esperados.

Payload bruto: `payloads/04_ad_groups.json`, `payloads/05_ads.json`.

---

## 5. Métricas — campanha, device e conversão

### 5.1 Últimos 30 dias (2026-08-02 a 2026-09-01)
Como só há 1 campanha ativa, a janela recente é pobre: 12 linhas de métrica diária, **device só `MOBILE`**, e **zero linhas** de breakdown por ação de conversão (apesar de existirem 48 ações de conversão cadastradas na conta — ver §6). Isso por si só já é um dado importante: **não dá pra validar o formato completo dos dados só olhando os últimos 30 dias desta conta.**

### 5.2 Janela ampla (2020-01-01 a 2026-09-01, sem segmentar por data)
Repeti a consulta de device e de ação de conversão numa janela de ~6 anos, sem `segments.date` (só agregado por campanha), pra pegar exemplos reais das campanhas antigas:

- **Device**: 4 valores reais encontrados — `MOBILE`, `DESKTOP`, `TABLET`, **`CONNECTED_TV`**. O `CONNECTED_TV` é importante: nenhuma documentação interna do projeto até agora mencionava esse valor (as notas anteriores só citavam MOBILE/DESKTOP/TABLET). Precisa entrar no enum/domínio de `device` do schema.
- **Ação de conversão**: 18 combinações campanha×ação com valor real. Exemplo direto do payload:

```json
{
  "campaign_name": "[GUARA] SEARCH BRANDED",
  "conversion_action_name": "Local actions - Website visits",
  "conversion_action_category": "PAGE_VIEW",
  "conversions": 0.0,
  "all_conversions": 47.0
}
```

Isso confirma na prática uma distinção que o schema precisa respeitar: **`conversions` só conta ações marcadas como meta primária** da conta; `all_conversions` conta *todas* as ações rastreadas, primárias ou não. Uma ação pode ter `conversions = 0` e `all_conversions = 47` ao mesmo tempo — não é bug, é o Google reportando duas métricas com semânticas diferentes por definição. O `0002_core_schema.sql` atual já tem os dois campos em `daily_metrics` (`platform_conversions`), mas só um valor — **falta um segundo par de colunas pra `all_conversions`/`all_conversions_value`** se o relatório for usar essa distinção (bem provável que sim, pra bater com o que a agência já vê no próprio Google Ads Manager).

Payload bruto: `payloads/06_daily_campaign_metrics.json`, `payloads/07_device_breakdown.json` (30 dias), `payloads/07b_device_breakdown_wide.json` (6 anos), `payloads/08b_conversion_action_wide.json`.

---

## 6. Catálogo de ações de conversão (`conversion_action`)

48 ações cadastradas na conta. Achados:

- Maioria (`~30`) está com `status = HIDDEN` — ainda existe e é rastreada (aparece em `all_conversions`), mas fica **fora** do relatório padrão/da métrica `conversions`. Isso reforça o ponto do §5.2: qualquer schema que só grave `conversions` (sem `all_conversions`) vai sistematicamente esconder a maior parte da atividade de conversão real dessa conta.
- Fontes bem heterogêneas: `UNIVERSAL_ANALYTICS_GOAL`, `GOOGLE_ANALYTICS_4_PURCHASE`/`GOOGLE_ANALYTICS_4_CUSTOM`, `FIREBASE_ANDROID_*` (eventos de app mobile), `GOOGLE_HOSTED` (cliques/direções do próprio Google), `SMART_CAMPAIGN_TRACKED_CALLS`. Ou seja, "ação de conversão" no Google Ads não é uma coisa só — é qualquer evento de qualquer fonte integrada (GA4, Firebase, chamadas, cliques em direção no mapa) que a conta decidiu importar.
- `category` (`PURCHASE`, `PAGE_VIEW`, `CONTACT`, `GET_DIRECTIONS`, `DOWNLOAD`, `ADD_TO_CART`, `BEGIN_CHECKOUT`, `ENGAGEMENT`, `DEFAULT`, ...) é o campo que dá o "tipo de negócio" da conversão — mais útil pra agregação/relatório do que o nome livre.

Payload bruto: `payloads/10_conversion_action_catalog.json`.

---

## 7. Geografia (`geographic_view`)

Funciona, 23 linhas na janela de 30 dias. Confirmado o ponto que já estava anotado na documentação anterior (e que eu havia deixado como "a validar"): **`country_criterion_id` vem como ID numérico puro** (ex.: `2600`, `2858`) — não vem nome de país. Pra virar um relatório legível ("Brasil: X impressões"), é obrigatório resolver esse ID contra o recurso `geo_target_constant` do Google (uma tabela de referência própria da API) — isso ainda não foi testado nesta exploração e fica como próximo passo se geografia entrar no escopo do relatório inicial.

Payload bruto: `payloads/09_geographic_view.json`.

---

## 8. O que isso muda em relação à documentação anterior

| Afirmação anterior | Situação real confirmada agora |
|---|---|
| "Conta de Teste/Produção: `4378571170`" | Não é conta de teste — é conta real de um cliente ativo da agência (Guararapes Internacional) |
| Device validado como MOBILE/DESKTOP/TABLET | Existe um 4º valor real: `CONNECTED_TV` |
| `geographic_view` "validado" | Segue funcionando, mas a limitação do ID numérico sem nome (já suspeitada) foi confirmada, não resolvida |
| Nenhuma menção a distinção `conversions` vs `all_conversions` no dado real | Confirmado com exemplo real que a diferença é grande e sistemática (a maioria das ações fica `HIDDEN`, só aparecendo em `all_conversions`) |
| — | **Novo**: só 1 de 36 campanhas está ativa — qualquer amostra de dado "recente" desta conta vai ser pobre; testes futuros de pipeline devem considerar isso |
| — | **Novo**: correlação `Clínica de Olhos Videira` (Ads) ↔ `hospital-de-olhos-videira` (Vault) |
| — | **Novo**: bug de GAQL (`campaign.start_date`/`end_date` não existem em v25) |

---

## 9. Pontos em aberto para a modelagem do banco (não resolvidos aqui, propositalmente)

- Como representar `conversions` **e** `all_conversions` sem duplicar toda a tabela de fato.
- Se `geographic_view` entra no MVP inicial ou fica pra depois (dado o trabalho extra de resolver `geo_target_constant`).
- Como tratar o fato de que `ads.name`/identidade do anúncio varia por tipo (não dá pra tratar como uma coluna simples e genérica pra todos os 7 tipos encontrados).
- Se orçamento de campanha (`campaign_budget.amount_micros`) volta pro schema ou fica de fora do MVP de relatório (schema atual não tem).

Isso fica pra quando os dois lados (Google + Meta) estiverem explorados.
