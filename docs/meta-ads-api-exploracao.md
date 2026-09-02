# Exploração da Meta Marketing API — Sync

> Exploração real (somente leitura, escopo `ads_read`) feita em 2026-09-01 contra 3 contas de anúncio reais da agência. Script ad-hoc (não faz parte do pipeline), payloads brutos em `docs/meta-ads-api-exploracao/payloads/*.json`.

---

## 0. Setup usado

- App **Sync** (`app_id 2570839423344539`), caso de uso "Mensurar dados de desempenho do anúncio com a API de Marketing", dentro do Business Portfolio **Tempero Propaganda**.
- Autenticação via **System User** (`Sync API`), token com escopo **só `ads_read`**, `expires_at: 0` e `data_access_expires_at: 0` — **não expira**. Confirmado via `/debug_token`.
- Contas testadas (todas com "ver desempenho" atribuído ao Sync API, nada de escrita):

| Apelido | Nome real | Business dono | Gasto histórico (`amount_spent`) |
|---|---|---|---|
| `aproest` | CA01 - Aproest | Associação de Benefícios do Oeste Catarinense (Aproest) | R$ 2.549 (centavos, ver nota) |
| `hospital_de_olhos` | **Hospital de Olhos Videira** | Clínica de Cirurgia de Olhos Videira LTDA | R$ 41.165,54 |
| `bom_preco` | Lojas Bom Preço | Móveis Bom Preço LTDA | R$ 6.191,28 |

> Nota: `amount_spent` vem em centavos como string (`"4116554"` = R$ 41.165,54) — mesma armadilha de precisão que já tratamos com `cost_micros` no Google, só que em base 100 em vez de base 1.000.000.

Versão da API usada: `v23.0` (Graph API). Chamadas via `requests` puro (REST), não usei o SDK oficial (`facebook-business`) — decisão deliberada pra essa fase de exploração, pra ver o JSON cru sem abstração de SDK no meio, igual ao espírito do que fizemos manualmente com os proto_plus do Google.

---

## 1. Achado mais importante: o array `actions` é uma bagunça organizada, e isso muda a modelagem

Isso é a coisa mais relevante que saiu dessa exploração, mais até que qualquer detalhe de campo.

No Google Ads, cada linha de `segments.conversion_action` trazia **uma ação por linha**, com um nome e categoria únicos (`conversion_action_name`, `conversion_action_category`). No Meta, o `/insights` devolve **um único campo `actions`, que é uma lista com todos os tipos de ação que aconteceram naquele contexto ao mesmo tempo** — e a mesma "coisa que aconteceu de verdade" costuma aparecer **múltiplas vezes, com nomes diferentes**, porque cada `action_type` representa uma janela de atribuição/fonte de medição diferente do mesmo evento.

Exemplo real de uma única campanha de geração de leads (`aproest`, campanha "LEADS_LP-FORM-NATIVO"), no mesmo payload, tudo relacionado a **lead**:

```
lead                                        → 912
onsite_conversion.lead                      → 5
onsite_conversion.lead_grouped              → 497
offsite_conversion.fb_pixel_lead            → 415
onsite_web_lead                             → 420
offsite_lead_add_20_s_calls                 → 415
offsite_complete_registration_add_meta_leads→ 497
offsite_search_add_meta_leads               → 497
offsite_content_view_add_meta_leads         → 497
```

**Nove `action_type` diferentes, nenhum deles com o mesmo valor, todos "sobre lead".** Isso não é bug nem inconsistência de dado — é assim que a Meta reporta por design (cada linha reflete uma combinação diferente de origem do sinal + janela de atribuição). O mesmo padrão se repete pra **purchase** em outra campanha da mesma conta (`purchase`, `onsite_conversion.purchase`, `omni_purchase`, `offsite_conversion.fb_pixel_purchase`, `onsite_web_purchase`, `onsite_web_app_purchase`, `web_in_store_purchase`, `web_app_in_store_purchase`, `offsite_purchase_add_20_s_calls` — 9 variantes de novo).

**Implicação direta pra modelagem:** não dá pra simplesmente gravar "cada `action_type` = uma linha de fato" sem estratégia, porque somar todos os `action_type` relacionados a lead numa campanha triplica/quadruplica a contagem real de leads. Vai precisar de uma decisão explícita (ainda em aberto, não resolvida aqui de propósito): escolher **um `action_type` canônico por categoria de negócio** (ex.: `lead` ou `onsite_conversion.lead_grouped` pra leads, `purchase` pra compras) e tratar os demais como metadado/atribuição alternativa, não como fatos adicionais a somar.

Também achei que `action_values` (valor em R$) só existe pra alguns `action_type` (normalmente os de compra/checkout) — ações de engajamento (like, comment, video_view) não têm valor monetário associado, o que faz sentido.

`cost_per_action_type` é **campo derivado** (gasto ÷ contagem daquele tipo de ação) — mesma lógica que o próprio projeto já aplica pro Google (CTR/CPC/CPM calculados, não armazenados): não precisa gravar isso cru, dá pra calcular na hora do relatório.

---

## 2. Correção de uma suposição minha: `action_breakdowns` não fatia em linhas separadas

Eu esperava que `action_breakdowns=action_type` fizesse a API devolver **uma linha por ação** (equivalente ao `segments.conversion_action` do Google). Não é isso — o array `actions` já vem com granularidade por `action_type` **por padrão**, mesmo sem pedir `action_breakdowns` explicitamente. O parâmetro `action_breakdowns` controla uma dimensão **dentro** de cada item do array (ex.: por dispositivo da ação), não separa em linhas diferentes. Registrando isso pra não repetir a suposição errada quando formos escrever o pipeline de verdade.

---

## 3. Hierarquia de entidades — confirma o paralelo com o Google Ads

```
Ad Account (act_...)
   └── Campaign        (objective, status, budget)
         └── Ad Set     (optimization_goal, billing_event, bid_strategy, budget)
               └── Ad   (creative: object_type, object_story_spec)
```

Mapeia limpo pro schema genérico que já temos (`ad_accounts` → `campaigns` → `ad_groups` → `ads`), sem precisar de tabela nova pra essa parte. Só um detalhe: `daily_budget` e `lifetime_budget` são mutuamente exclusivos (um vem `"0"` quando o outro está em uso) — mesmo padrão conceitual do `budget_type`/`budget_amount` que existia no schema v1 do projeto.

**Objetivos de campanha encontrados** (campo `objective`), variam bastante entre contas — e revelam contas com histórico bem antigo:

| Conta | Objetivos encontrados |
|---|---|
| `aproest` | `OUTCOME_AWARENESS`, `OUTCOME_ENGAGEMENT`, `OUTCOME_LEADS`, `OUTCOME_TRAFFIC` |
| `hospital_de_olhos` | `OUTCOME_AWARENESS`, `OUTCOME_ENGAGEMENT`, `OUTCOME_LEADS`, `OUTCOME_TRAFFIC`, **+ `LINK_CLICKS`, `POST_ENGAGEMENT`, `REACH`, `VIDEO_VIEWS`** (nomenclatura antiga, pré-2022, da época em que a Meta ainda não tinha migrado pros objetivos `OUTCOME_*`) |
| `bom_preco` | `OUTCOME_AWARENESS`, `OUTCOME_ENGAGEMENT`, `OUTCOME_TRAFFIC` |

A conta do Hospital de Olhos tem campanha ativa há tempo suficiente pra carregar as duas gerações de nomenclatura de objetivo — vale considerar isso ao decidir se o schema trata `objective` como enum fechado ou texto livre (recomendo texto livre / lookup, não enum rígido, exatamente pelo mesmo motivo que já discutimos pro `campaign_type` do lado Google).

---

## 4. Confirma de novo o padrão "poucas campanhas ativas, muito histórico morto"

Igual aconteceu no Google Ads: `bom_preco` tem **690 campanhas no total**, mas ao pedir insights dos últimos 90 dias **só 2 campanhas retornaram alguma linha** (o resto não teve nenhuma impressão no período — a API simplesmente não retorna linha pra combinação sem dado, não retorna zero explícito). Isso confirma que decisões de pipeline (histórico vs. incremental) precisam lidar bem com contas de anos de operação onde a fração realmente ativa é pequena — não é peculiaridade da conta do Google, é o padrão real do jeito que essas contas de agência acumulam campanha ao longo do tempo.

Isso também foi o que causou o único erro técnico dessa exploração: pedir métricas **diárias** (`time_increment: 1`) pro nível de campanha nos últimos 90 dias pra uma conta com 690 campanhas gerou uma consulta pesada o suficiente pra estourar timeout de 30s. Resolvido aumentando o timeout e trocando pra consulta agregada (sem quebrar por dia) — antes de qualquer pipeline real, isso vira uma decisão de design: paginar por período menor, ou pedir relatório assíncrono (a Marketing API tem um modo de "insights job" assíncrono pra volumes grandes, ainda não testado aqui).

---

## 5. Breakdowns (device/plataforma)

Funciona igual ao esperado, uma linha por combinação de dimensão:

```json
{
  "campaign_id": "...",
  "impressions": "135",
  "clicks": "12",
  "actions": [...],
  "publisher_platform": "audience_network",
  "platform_position": "an_classic",
  "impression_device": "android_smartphone"
}
```

Valores reais encontrados:
- `impression_device`: `android_smartphone`, `android_tablet`, `desktop`, `ipad`, `iphone`, `other` — mais granular que o `segments.device` do Google (que só dava MOBILE/DESKTOP/TABLET/CONNECTED_TV), porque já separa Android de iOS.
- `publisher_platform`: `facebook`, `instagram`, `audience_network`, `threads`, `unknown` — isso **não existe no Google Ads**: é a rede dentro do ecossistema Meta onde o anúncio rodou. Precisa de dimensão própria no schema, não tem equivalente direto do lado Google.

---

## 6. Ads / criativos

`ad.creative.object_type` encontrado: `STATUS`, `SHARE`, `VIDEO` (na amostra). O campo `name` do criativo geralmente é o **próprio texto do anúncio truncado + timestamp/hash gerado automaticamente** (ex.: `"👁️ A boa visão faz diferença para qualquer pessoa... 2026-08-26-3f465c698ad682a7761ec99e09dabd5f"`), não um nome escolhido manualmente — parecido com o achado do Google de que `ads.name` nem sempre é um identificador limpo, só que aqui pelo menos sempre vem preenchido (o problema do Google era campo vazio pra alguns tipos).

---

## 7. Confirmação direta: o conteúdo bate com o Vault

A conta do Hospital de Olhos tem anúncios com nomes/copy como **"008_Famosos e Cirurgia"**, **"007_Reel_Contra Indicações"**, **"001_TransPRK Por Dentro"** — "TransPRK" é uma técnica de cirurgia refrativa a laser. Isso bate exatamente com o que está documentado em `vault/Sync/clientes/hospital-de-olhos-videira/cliente.md` (prioridade comercial #1 = Cirurgia Refrativa a Laser). Primeira vez que confirmamos essa correlação Vault↔dado de anúncio **com conteúdo real dos dois lados**, não só pelo nome do cliente — é exatamente o caso de uso que o Sync deveria habilitar no fim (cruzar contexto do Vault com métrica real).

---

## 8. Problemas encontrados durante a configuração (não são bugs da Meta)

1. **App Secret colado errado** — `META_APP_SECRET` acabou com o mesmo valor de `META_APP_ID` por engano ao preencher o `.env.admin`. Causou erro 190 (`Invalid OAuth access token signature`) no `/debug_token`. Resolvido recopiando o valor certo da tela "Configurações do app → Básico".
2. **Falha transitória isolada** no `/debug_token` durante a primeira tentativa de rodar o script completo (erro 100, "not an owner or developer") — não se repetiu ao testar de novo isoladamente segundos depois, nem afetou nenhuma chamada de dado real. Tratando como instabilidade pontual da API, não como problema de configuração.
3. **Timeout em conta grande** — já descrito no item 4.

---

## 9. Comparação rápida com os achados do Google Ads

| Aspecto | Google Ads | Meta Marketing API |
|---|---|---|
| Ação de conversão | 1 linha por ação (`segments.conversion_action`) | Todas as ações juntas num array `actions`, com redundância entre `action_type` |
| Device | 4 valores (inclui CONNECTED_TV) | 6 valores (separa Android/iOS/tablet/desktop/other) |
| Dimensão de rede/canal | Não existe (é tudo "Google") | `publisher_platform` (facebook/instagram/audience_network/threads) — sem equivalente no Google |
| "Poucas campanhas ativas, muito histórico" | Confirmado (1 de 36 ativa) | Confirmado (2 de 690 com dado em 90 dias) |
| Token de longa duração | Exige publicar o app fora do modo Testing (pendente, não resolvido) | Resolvido — System User com token sem expiração, já funcionando |
| Precisão monetária | `cost_micros` (base 1.000.000) | `amount_spent`/`spend` em string decimal direta (sem micros) — mais simples de lidar |

---

## 10. Pontos em aberto para a modelagem (propositalmente não resolvidos aqui)

- Como escolher o(s) `action_type` canônico(s) por categoria de negócio (lead, mensagem, compra) sem perder a granularidade de atribuição pra quem quiser aprofundar depois.
- Se `publisher_platform`/`platform_position` viram uma dimensão dentro da mesma tabela de fato genérica que pensamos pro Google (`metric_dimensions`), ou se cada plataforma acaba precisando da própria tabela de dimensão por serem conceitos muito diferentes entre Google/Meta.
- Estratégia de paginação/janela pra contas grandes (690 campanhas) antes de qualquer sync incremental real — investigar o modo assíncrono de relatório da Marketing API.
- Ainda não testamos Lead Ads nativo (formulário dentro do próprio Meta, sem ir pro site) nem paginação além de 10 páginas — os `action_type` relacionados a lead que vimos aqui vieram de pixel/CRM externo, não do formulário nativo da Meta.
