# SYNC — AI GUIDE
## Guia Operacional e de Segurança para Agentes de IA

**Arquivo:** `AI_GUIDE.md`  
**Localização obrigatória:** raiz do projeto `sync/`  
**Status:** versão inicial de segurança / ambiente de testes  
**Objetivo:** orientar o agente de IA sobre como trabalhar no projeto Sync sem conceder permissões por conta própria.

---

# 0. REGRA CRÍTICA — LEITURA OBRIGATÓRIA

## 0.1 Antes de qualquer ação

Ao receber qualquer mensagem, pergunta, solicitação, tarefa ou comando relacionado ao projeto `sync`, a **primeira ação operacional do agente DEVE ser ler este arquivo completo**:

```text
/AI_GUIDE.md
```

Nenhuma das ações abaixo deve ocorrer antes dessa leitura:

- executar comandos;
- executar Python;
- executar scripts;
- consultar dados;
- acessar o banco;
- modificar arquivos;
- criar arquivos;
- apagar arquivos;
- acessar a rede;
- utilizar MCP;
- procurar ferramentas adicionais;
- alterar configurações;
- iniciar automações.

## 0.2 Se o arquivo não puder ser lido

Se `AI_GUIDE.md` estiver ausente, inacessível, vazio, corrompido ou não puder ser interpretado:

**PARAR.**

O agente deve informar que não pode prosseguir com ações operacionais até que o guia esteja disponível.

Não é permitido reconstruir, presumir ou inventar as regras deste arquivo.

## 0.3 O guia não concede permissões

Este documento define o comportamento esperado do agente.

Ele **não concede permissões técnicas**.

Uma permissão bloqueada pelo ambiente do Antigravity continua bloqueada mesmo que este documento diga que uma ação seria útil.

A segurança técnica do ambiente sempre deve prevalecer.

---

# 1. OBJETIVO DO PROJETO

O Sync é um laboratório pessoal para integrar:

```text
CONHECIMENTO
    ↓
Arquivos Markdown / Vault

DADOS
    ↓
MariaDB

PROCESSAMENTO
    ↓
Python

INTELIGÊNCIA
    ↓
Agente de IA
```

O objetivo é permitir que o agente utilize conhecimento documental e dados estruturados para responder perguntas e realizar análises controladas.

A arquitetura do projeto foi planejada para separar:

- conhecimento;
- dados;
- processamento;
- inteligência.

O projeto deve evoluir de forma incremental, validando cada etapa antes de ampliar permissões ou automações.

---

# 2. HIERARQUIA DE REGRAS

Ao tomar qualquer decisão, utilizar esta ordem de prioridade:

1. **Políticas e restrições do sistema/plataforma**
2. **Permissões técnicas configuradas no ambiente**
3. **Este `AI_GUIDE.md`**
4. **Documentação técnica do projeto**
5. **Solicitação do usuário**
6. **Inferências ou conveniências do agente**

Uma regra de nível inferior nunca pode substituir uma regra de nível superior.

Exemplo:

> O usuário pede para acessar diretamente o banco.

Isso não autoriza o agente a fazer isso se o ambiente ou este guia proibir a ação.

---

# 3. PRINCÍPIO FUNDAMENTAL DE SEGURANÇA

## 3.1 O agente não possui acesso direto ao banco

O agente de IA **NÃO DEVE acessar o MariaDB diretamente**.

Isso inclui:

- abrir o banco;
- criar conexão própria com o banco;
- descobrir credenciais;
- procurar arquivos de configuração contendo credenciais;
- executar SQL diretamente;
- abrir um cliente SQL;
- utilizar ferramentas externas para consultar o banco;
- criar conexões improvisadas;
- alterar configurações para obter acesso ao banco.

O acesso aos dados deve ocorrer através de uma camada Python explicitamente criada e documentada para esse propósito.

Fluxo esperado:

```text
Usuário
   ↓
Agente de IA
   ↓
AI_GUIDE.md
   ↓
Identificação da necessidade
   ↓
Script Python autorizado
   ↓
Banco
   ↓
Resultado controlado
   ↓
Agente de IA
   ↓
Usuário
```

Fluxo proibido:

```text
Agente de IA
   ↓
MariaDB diretamente
```

---

# 4. PRINCÍPIO DE MÍNIMO PRIVILÉGIO

O agente deve utilizar somente os recursos estritamente necessários para responder à solicitação.

Não é permitido:

- procurar informações "por garantia";
- acessar arquivos não relacionados à tarefa;
- executar scripts não relacionados;
- consultar tabelas desnecessárias;
- buscar credenciais;
- ampliar permissões;
- criar novas ferramentas sem necessidade;
- habilitar MCP;
- habilitar acesso de rede;
- alterar configurações de segurança.

Quando houver dúvida sobre a necessidade de um acesso:

**não executar.**

Solicitar confirmação ao usuário ou informar a limitação.

---

# 5. ESTADO ATUAL DO PROJETO

O projeto está em **ambiente de testes**.

Os dados atuais devem ser tratados como dados de desenvolvimento/teste.

Mesmo assim, o comportamento deve seguir desde já as regras que serão utilizadas posteriormente com dados reais.

A intenção é encontrar erros de arquitetura, permissões e comportamento enquanto o ambiente ainda está controlado.

---

# 6. FONTES DE INFORMAÇÃO

O Sync possui duas fontes conceituais principais.

## 6.1 Vault / Markdown

O Vault contém conhecimento contextual.

Exemplos:

```text
briefing.md
cliente.md
produtos.md
publico-alvo.md
tom-de-voz.md
estrategia.md
reunioes/*.md
```

Esses arquivos podem conter:

- contexto do cliente;
- produtos;
- serviços;
- público-alvo;
- posicionamento;
- tom de voz;
- briefings;
- estratégias;
- observações;
- decisões de reuniões;
- contexto de campanhas.

O Obsidian é uma interface sobre esses arquivos. Ele não é considerado o banco de dados do projeto.

## 6.2 MariaDB

O MariaDB contém dados estruturados.

O schema atual contempla entidades como:

```text
clients
platforms
ad_accounts
campaigns
ad_groups
ads
daily_metrics
landing_pages
leads
conversions
schema_migrations
```

As métricas diárias são armazenadas em `daily_metrics`, enquanto indicadores derivados como CTR, CPC e CPM podem ser calculados a partir dos dados-base.

---

# 7. PYTHON COMO CAMADA CONTROLADA

Python é a camada intermediária entre o agente e os dados estruturados.

O Python poderá futuramente:

- consultar dados;
- processar dados;
- integrar APIs;
- ler arquivos;
- transformar informações;
- preparar resultados;
- alimentar outras partes do projeto.

Entretanto, cada capacidade deve ser implementada através de scripts ou módulos explicitamente documentados.

O agente **não deve criar uma consulta SQL improvisada para responder uma pergunta**.

---

# 8. REGRA PARA UTILIZAÇÃO DOS SCRIPTS PYTHON

## 8.1 O agente deve escolher um script existente

Ao receber uma pergunta que exige dados estruturados:

1. Ler `AI_GUIDE.md`.
2. Identificar qual informação é necessária.
3. Consultar o catálogo de scripts deste guia.
4. Verificar se existe um script adequado.
5. Utilizar somente o script apropriado.
6. Antes de executar, informar claramente o que pretende executar quando isso for necessário para aprovação.
7. Solicitar/apresentar a execução ao mecanismo de aprovação do ambiente.
8. Interpretar somente o resultado retornado pelo script.
9. Responder ao usuário.

## 8.2 Não existe script adequado

Se não existir um script adequado:

**NÃO criar automaticamente uma consulta improvisada ao banco.**

O agente deve informar:

> "Não existe atualmente um script autorizado para consultar esse tipo de informação."

Depois, pode sugerir que seja criado um novo script.

A criação do novo script deve ser uma etapa separada.

## 8.3 Não alterar scripts para obter uma resposta

O agente não deve modificar um script existente apenas para contornar uma limitação ou obter dados adicionais durante uma consulta.

Se for necessário ampliar a capacidade:

1. explicar a necessidade;
2. propor a alteração;
3. aguardar aprovação;
4. implementar/testar separadamente.

---

# 9. SCRIPTS DE CONSULTA — REGRAS DE SEGURANÇA

Os scripts destinados ao agente devem, preferencialmente:

- possuir finalidade única;
- receber parâmetros explícitos;
- validar parâmetros;
- utilizar consultas parametrizadas;
- possuir limites de quantidade de registros;
- retornar resultados estruturados;
- evitar informações desnecessárias;
- não retornar credenciais;
- não retornar segredos;
- não modificar dados quando forem scripts de consulta.

## 9.1 Scripts de consulta devem ser somente leitura

Um script classificado como:

```text
READ_ONLY
```

não pode:

- INSERT;
- UPDATE;
- DELETE;
- DROP;
- ALTER;
- TRUNCATE;
- CREATE;
- GRANT;
- REVOKE.

O agente não deve transformar um script de leitura em ferramenta de escrita.

---

# 10. PROIBIÇÃO DE ALTERAÇÃO DE DADOS

Durante esta fase do projeto, o agente não deve alterar dados do banco.

Isso inclui:

```text
INSERT
UPDATE
DELETE
TRUNCATE
DROP
ALTER
CREATE
```

qualquer outra operação equivalente.

Se uma tarefa exigir alteração de dados, o agente deve parar e solicitar instruções explícitas para uma etapa específica de desenvolvimento.

---

# 11. PROIBIÇÃO DE EXECUÇÃO ARBITRÁRIA

O agente não deve executar comandos simplesmente porque parecem úteis.

Exemplos de comportamento proibido:

```text
"Vou abrir o banco para descobrir a estrutura."
"Vou procurar as credenciais."
"Vou testar alguns SELECTs."
"Vou instalar uma biblioteca."
"Vou rodar todos os scripts para ver o que existe."
"Vou procurar na internet."
"Vou habilitar um MCP."
```

O agente deve seguir o fluxo documentado.

---

# 12. EXECUÇÃO DE TERMINAL

A execução de comandos deve permanecer sujeita às permissões do ambiente do Antigravity.

O agente não deve:

- tentar contornar uma aprovação;
- tentar executar o comando de outra forma para evitar aprovação;
- alterar configurações de segurança para facilitar uma execução;
- utilizar comandos alternativos para burlar uma restrição;
- executar comandos fora do escopo da tarefa.

Se uma execução for bloqueada:

**não tentar contornar o bloqueio.**

---

# 13. ACESSO A ARQUIVOS

O agente deve acessar somente os arquivos necessários para a tarefa.

Não deve procurar arquivos fora do projeto `sync`.

Não deve:

- procurar arquivos pessoais;
- procurar credenciais;
- procurar chaves privadas;
- procurar tokens;
- procurar arquivos de outros projetos;
- procurar arquivos do sistema;
- tentar sair das pastas autorizadas.

Se uma informação necessária estiver fora do escopo autorizado:

**parar e informar a limitação.**

---

# 14. SEGREDOS E CREDENCIAIS

O agente não deve procurar, expor ou manipular desnecessariamente:

- senhas;
- tokens;
- API keys;
- chaves privadas;
- credenciais do banco;
- secrets;
- arquivos `.env`;
- credenciais de serviços externos.

Mesmo que um arquivo contendo credenciais esteja acessível ao projeto, o agente não deve revelar seu conteúdo ao usuário.

Credenciais nunca devem aparecer em respostas, logs ou resultados de scripts.

---

# 15. REDE

O agente não deve utilizar acesso de rede para responder perguntas do Sync durante esta fase, salvo quando uma futura etapa do projeto autorizar explicitamente essa capacidade.

Não deve:

- acessar APIs diretamente;
- pesquisar a internet;
- baixar arquivos;
- enviar dados;
- instalar dependências;
- chamar serviços externos.

As integrações externas serão implementadas posteriormente e de maneira controlada pelo código Python.

---

# 16. MCP

Nenhum MCP deve ser utilizado atualmente para acessar dados do Sync.

Não adicionar, habilitar ou configurar MCP por iniciativa própria.

Se futuramente houver necessidade de MCP:

1. definir o objetivo;
2. documentar o MCP;
3. definir permissões;
4. testar em ambiente controlado;
5. atualizar este guia;
6. somente então habilitar.

---

# 17. COMO RESPONDER A UMA PERGUNTA

Para cada pergunta:

```text
ETAPA 1
Ler AI_GUIDE.md

        ↓

ETAPA 2
Classificar a pergunta

        ↓

ETAPA 3
Identificar a fonte necessária

        ↓

ETAPA 4
Se for Vault:
consultar somente os arquivos necessários

        ↓

ETAPA 5
Se forem dados estruturados:
procurar um script Python autorizado

        ↓

ETAPA 6
Se houver script:
executá-lo somente através do mecanismo autorizado

        ↓

ETAPA 7
Validar o resultado

        ↓

ETAPA 8
Responder
```

---

# 18. CLASSIFICAÇÃO DAS PERGUNTAS

## Tipo A — Conhecimento documental

Exemplo:

> "Qual é o público-alvo do Cliente X?"

Fonte provável:

```text
Vault
```

Não executar Python se os dados já estiverem disponíveis no Vault.

---

## Tipo B — Dados quantitativos

Exemplo:

> "Quanto foi investido na campanha X?"

Fonte provável:

```text
MariaDB
```

Utilizar um script Python autorizado.

O usuário não precisa informar o nome do script. O agente deve consultar o catálogo e escolher a ferramenta adequada com base na intenção da pergunta.

---

## Tipo C — Análise combinada

Exemplo:

> "Com base no posicionamento do cliente e nos resultados das campanhas, o que deveríamos testar?"

Fontes:

```text
Vault
+
MariaDB
```

O agente deve consultar cada fonte pelo mecanismo autorizado e então realizar a análise.

---

## Tipo D — Solicitação operacional

Exemplo:

> "Atualize os dados da campanha."

Isso não é uma simples consulta.

O agente deve verificar se existe uma ferramenta/script explicitamente autorizado para escrita.

Se não existir:

**não executar.**

---

# 19. RESULTADOS DOS SCRIPTS

Os scripts devem retornar resultados fáceis de interpretar.

Preferencialmente:

```text
JSON
```

ou uma estrutura equivalente claramente delimitada.

Exemplo:

```json
{
  "status": "success",
  "query_type": "campaign_performance",
  "client": "cliente-x",
  "period": {
    "start": "2026-01-01",
    "end": "2026-03-31"
  },
  "data": []
}
```

O agente deve distinguir:

```text
status = success
```

de:

```text
status = error
```

Se houver erro, não inventar resultados.

---

# 20. INTEGRIDADE DOS RESULTADOS

O agente não deve:

- inventar dados;
- completar dados ausentes com suposições;
- tratar erro como resultado válido;
- esconder que uma consulta falhou;
- apresentar estimativas como dados reais;
- misturar dados de clientes diferentes;
- alterar silenciosamente filtros;
- remover registros apenas para melhorar uma resposta.

Se os dados forem insuficientes:

**informar a limitação.**

---

# 21. IDENTIFICAÇÃO DO CLIENTE

Sempre que uma consulta envolver cliente, o agente deve evitar ambiguidade.

Se houver dúvida sobre qual cliente está sendo solicitado:

**perguntar antes de executar a consulta.**

Nunca assumir silenciosamente um cliente apenas porque parece provável.

---

# 22. PERÍODO DE CONSULTA

Quando uma pergunta envolver datas:

- interpretar explicitamente o período;
- confirmar quando houver ambiguidade;
- não inventar datas;
- não ampliar o período sem informar;
- não reduzir o período silenciosamente.

Exemplo:

> "últimos três meses"

Deve resultar em um período claramente identificado na consulta e, quando apropriado, apresentado na resposta.

---

# 23. LIMITAÇÃO DE RESULTADOS

Scripts de consulta devem possuir limites razoáveis.

O agente não deve solicitar grandes volumes de dados apenas para "analisar depois".

Preferir:

```text
agregações
resumos
rankings
métricas
períodos
filtros
```

em vez de retornar milhares de registros individuais.

Quando uma pergunta puder ser respondida por uma agregação, preferir a agregação.

---

# 24. ERROS E SITUAÇÕES INESPERADAS

Se um script retornar erro:

1. não ocultar o erro;
2. não inventar uma resposta;
3. não modificar o script automaticamente para contornar o problema;
4. não executar consultas alternativas improvisadas;
5. informar o problema;
6. sugerir o próximo passo.

Exemplo:

> "O script `X` falhou ao consultar os dados. Não vou tentar acessar o banco diretamente. Precisamos verificar o script/conexão."

---

# 25. NOVOS SCRIPTS

Novos scripts devem ser criados de forma incremental.

Antes de um novo script ser considerado autorizado para uso pelo agente, ele deve possuir:

- nome claro;
- finalidade;
- parâmetros;
- fonte dos dados;
- tipo de operação;
- indicação se é somente leitura;
- formato de saída;
- limites;
- tratamento de erros;
- testes;
- entrada no catálogo deste arquivo.

Até estar documentado e testado:

**não considerar o script autorizado.**

---

# 26. CATÁLOGO DE SCRIPTS AUTORIZADOS

Esta seção contém as únicas ferramentas Python de consulta ao MariaDB atualmente autorizadas para uso pelo agente.

Um script só pode ser considerado autorizado quando estiver documentado nesta seção, testado isoladamente e marcado como `VALIDADO`.

## Convenção

Cada script deverá possuir uma ficha:

```text
Nome:
Caminho:
Tipo:
Finalidade:
Entrada:
Saída:
Fonte:
Somente leitura:
Limites:
Status:
```

## 26.1 `get_client_info`

**Nome:** `get_client_info`  
**Caminho:** `src/ai_tools/get_client_info.py`  
**Tipo:** `READ_ONLY`  
**Finalidade:** Consultar informações básicas de um cliente.

**Entrada:**

```text
--client <client_slug>
```

**Exemplo:**

```text
python -m src.ai_tools.get_client_info --client seed-alpha-imoveis
```

**Saída:**

Retorna informações básicas do cliente, incluindo:

- id;
- nome;
- slug;
- segmento/industry;
- status;
- data de criação;
- data de atualização.

**Fonte:**

```text
MariaDB
└── clients
```

**Somente leitura:** `SIM`

**Limites:**

- aceita somente o slug exato do cliente;
- retorna no máximo um cliente;
- não aceita SQL arbitrário;
- não permite INSERT;
- não permite UPDATE;
- não permite DELETE;
- não executa migrations.

**Status:** `VALIDADO`

---

## 26.2 `get_client_campaigns`

**Nome:** `get_client_campaigns`  
**Caminho:** `src/ai_tools/get_client_campaigns.py`  
**Tipo:** `READ_ONLY`  
**Finalidade:** Listar as campanhas pertencentes a um cliente.

**Entrada:**

```text
--client <client_slug>
```

**Exemplo:**

```text
python -m src.ai_tools.get_client_campaigns --client seed-alpha-imoveis
```

**Saída:**

Retorna as campanhas do cliente, incluindo:

- id;
- identificador externo;
- nome;
- objetivo;
- status;
- tipo de orçamento;
- valor do orçamento;
- datas;
- conta de anúncios;
- plataforma.

**Fonte:**

```text
MariaDB
├── clients
├── ad_accounts
├── platforms
└── campaigns
```

**Somente leitura:** `SIM`

**Limites:**

- consulta somente campanhas pertencentes ao cliente informado;
- não aceita SQL arbitrário;
- não permite INSERT;
- não permite UPDATE;
- não permite DELETE;
- não executa migrations.

**Status:** `VALIDADO`

---

## 26.3 `get_campaign_performance`

**Nome:** `get_campaign_performance`  
**Caminho:** `src/ai_tools/get_campaign_performance.py`  
**Tipo:** `READ_ONLY`  
**Finalidade:** Consultar o desempenho de uma campanha em determinado período.

**Entrada:**

```text
--client <client_slug>
--campaign <campaign_id>
--start <YYYY-MM-DD>
--end <YYYY-MM-DD>
```

**Exemplo:**

```text
python -m src.ai_tools.get_campaign_performance --client seed-alpha-imoveis --campaign 1001 --start 2026-07-01 --end 2026-07-31
```

**Saída:**

Retorna:

- informações da campanha;
- período consultado;
- impressões;
- cliques;
- investimento;
- alcance;
- visualizações de vídeo;
- conversões da plataforma;
- CTR;
- CPC;
- CPM.

**Fonte:**

```text
MariaDB
├── clients
├── campaigns
├── ad_groups
├── ads
└── daily_metrics
```

**Somente leitura:** `SIM`

**Limites:**

- consulta uma campanha por execução;
- exige cliente e período;
- não aceita SQL arbitrário;
- não permite INSERT;
- não permite UPDATE;
- não permite DELETE;
- não executa migrations.

**Status:** `VALIDADO`

---

## 26.4 `get_client_conversions`

**Nome:** `get_client_conversions`  
**Caminho:** `src/ai_tools/get_client_conversions.py`  
**Tipo:** `READ_ONLY`  
**Finalidade:** Consultar as conversões registradas para um cliente em determinado período.

**Entrada:**

```text
--client <client_slug>
--start <YYYY-MM-DD>
--end <YYYY-MM-DD>
```

**Exemplo:**

```text
python -m src.ai_tools.get_client_conversions --client seed-alpha-imoveis --start 2026-07-01 --end 2026-07-31
```

**Saída:**

Retorna:

- período consultado;
- quantidade total de conversões;
- valor total das conversões;
- quantidade de conversões por tipo;
- registros individuais de conversão;
- campanha associada quando disponível.

**Fonte:**

```text
MariaDB
├── clients
├── conversions
└── campaigns
```

**Somente leitura:** `SIM`

**Limites:**

- consulta somente conversões pertencentes ao cliente informado;
- exige período;
- não aceita SQL arbitrário;
- não permite INSERT;
- não permite UPDATE;
- não permite DELETE;
- não executa migrations.

**Status:** `VALIDADO`

---

## Regra geral do catálogo

Os scripts acima são as **únicas ferramentas Python de consulta ao MariaDB atualmente autorizadas para uso pelo agente**.

O agente:

- pode escolher entre elas conforme a pergunta do usuário;
- pode utilizar mais de uma ferramenta quando uma pergunta exigir informações provenientes de fontes diferentes;
- deve escolher a ferramenta com base na finalidade da pergunta;
- não deve executar todas as ferramentas por precaução;
- não deve executar uma ferramenta apenas para descobrir o que ela retorna;
- não deve modificar os scripts durante uma consulta;
- não deve criar SQL alternativo caso uma ferramenta não seja suficiente.

O usuário final **não precisa conhecer o nome dos scripts**. A escolha da ferramenta é responsabilidade do agente.

Se nenhuma ferramenta existente for adequada para responder à pergunta:

**não improvisar.**

O agente deve informar que não possui atualmente uma ferramenta autorizada capaz de obter aquela informação. A criação ou alteração de uma ferramenta deve ocorrer em uma etapa separada de desenvolvimento, seguindo a seção 25.

---

# 26.5 REGRA DE DECISÃO DE FERRAMENTAS

O agente deve mapear a intenção da pergunta para a ferramenta adequada.

### Perguntas sobre informações básicas de um cliente

Utilizar:

```text
get_client_info
```

Exemplo:

> "Quem é a Alpha Imóveis?"

---

### Perguntas sobre campanhas de um cliente

Utilizar:

```text
get_client_campaigns
```

Exemplo:

> "Quais campanhas a Alpha Imóveis possui?"

---

### Perguntas sobre desempenho de uma campanha

Utilizar:

```text
get_campaign_performance
```

Exemplo:

> "Quanto a campanha Pesquisa - Imóveis gastou em julho?"

---

### Perguntas sobre conversões de um cliente

Utilizar:

```text
get_client_conversions
```

Exemplo:

> "Quantas conversões a Alpha Imóveis teve em julho?"

---

### Perguntas que exigem múltiplas ferramentas

Uma pergunta pode exigir mais de uma ferramenta autorizada.

Exemplo:

> "Compare o desempenho das campanhas da Alpha Imóveis e diga qual teve melhor resultado."

O agente poderá:

1. identificar as campanhas através de `get_client_campaigns`;
2. consultar o desempenho necessário através de `get_campaign_performance`;
3. comparar os resultados;
4. apresentar a conclusão baseada exclusivamente nos dados retornados.

O agente deve utilizar somente as ferramentas necessárias.

Não executar ferramentas adicionais apenas por precaução.

---

### O usuário não precisa conhecer as ferramentas

O usuário final pode fazer perguntas em linguagem natural sem mencionar scripts, caminhos ou parâmetros técnicos.

O agente deve identificar internamente qual ferramenta autorizada corresponde à necessidade da pergunta.

Exemplo:

> "Me diga quais campanhas da Alpha Imóveis estão ativas."

O agente deve identificar que `get_client_campaigns` é a ferramenta relevante e utilizar somente os dados retornados por ela.

Se a pergunta não puder ser respondida adequadamente pelas ferramentas disponíveis, o agente deve informar a limitação em vez de criar uma consulta improvisada.

# 27. CONVENÇÃO DE NOMES

Os scripts deverão possuir nomes descritivos.

Exemplos futuros:

```text
src/
└── ai_tools/
    ├── get_client_summary.py
    ├── get_campaign_performance.py
    ├── get_campaigns.py
    ├── get_period_summary.py
    └── get_conversion_summary.py
```

Os nomes são apenas exemplos.

Um script somente passa a ser autorizado depois de documentado e testado.

---

# 28. ESTRUTURA ESPERADA DO PROJETO

A estrutura poderá evoluir, mas conceitualmente:

```text
sync/
│
├── AI_GUIDE.md
│
├── src/
│   └── ...
│
├── vault/
│   └── ...
│
├── database/
│   └── ...
│
└── ...
```

O `AI_GUIDE.md` permanece na raiz para funcionar como referência central do comportamento do agente.

---

# 29. PRINCÍPIO DE NÃO AUTOMAÇÃO

O fato de uma tarefa poder ser automatizada não significa que ela deve ser automatizada.

Durante a fase de testes:

```text
automação mínima
+
aprovação humana
+
observabilidade
+
dados falsos/controlados
```

A automação deve aumentar somente depois que o comportamento tiver sido validado.

---

# 30. PRINCÍPIO DE CONFIRMAÇÃO

Quando uma ação puder:

- alterar dados;
- alterar arquivos importantes;
- criar efeitos externos;
- enviar informações;
- modificar configurações;
- instalar componentes;
- ampliar permissões;

o agente deve parar e solicitar confirmação antes da ação.

---

# 31. NÃO CONTORNAR REGRAS

É proibido tentar contornar qualquer regra deste guia através de:

- comandos equivalentes;
- comandos indiretos;
- scripts temporários;
- shell;
- PowerShell;
- subprocessos;
- outros interpretadores;
- ferramentas externas;
- MCP;
- APIs;
- alterações de configuração;
- criação de arquivos auxiliares;
- execução de código embutido.

Se uma ação estiver bloqueada:

**a ação está bloqueada.**

---

# 32. TESTES

Todos os novos componentes devem ser testados primeiro com dados falsos ou controlados.

Fluxo recomendado:

```text
Criar
 ↓
Testar isoladamente
 ↓
Validar resultado
 ↓
Documentar
 ↓
Adicionar ao catálogo
 ↓
Testar através do agente
 ↓
Somente depois considerar ampliar a capacidade
```

Não pular etapas.

---

# 33. CRITÉRIO PARA CONSIDERAR UMA FERRAMENTA SEGURA

Uma ferramenta Python destinada ao agente deve responder claramente:

1. O que ela faz?
2. Que dados ela acessa?
3. Que parâmetros aceita?
4. O que ela retorna?
5. Ela altera alguma coisa?
6. Qual é o limite da consulta?
7. Como trata erros?
8. Como sabemos que ela não está fazendo mais do que deveria?

Se essas perguntas não puderem ser respondidas:

**a ferramenta ainda não está pronta para ser utilizada pelo agente.**

---

# 34. PRINCÍPIO FINAL

O agente deve preferir:

```text
PARAR
+
EXPLICAR A LIMITAÇÃO
+
PEDIR CONFIRMAÇÃO
```

em vez de:

```text
ASSUMIR
+
EXECUTAR
+
TENTAR CORRIGIR DEPOIS
```

Em caso de dúvida, a opção segura é não executar.

---

# 35. CHECKLIST OPERACIONAL

Antes de qualquer ação operacional:

- [ ] Li este `AI_GUIDE.md`.
- [ ] Entendi a solicitação.
- [ ] Identifiquei a fonte de informação necessária.
- [ ] Verifiquei se existe um script autorizado.
- [ ] A ferramenta escolhida corresponde diretamente à necessidade da pergunta.
- [ ] A ferramenta escolhida está marcada como `VALIDADO` no catálogo.
- [ ] Não estou executando ferramentas desnecessárias.
- [ ] Não estou tentando acessar o banco diretamente.
- [ ] Não estou procurando credenciais.
- [ ] Não estou ampliando permissões.
- [ ] Não estou utilizando rede sem autorização.
- [ ] Não estou utilizando MCP.
- [ ] Não estou executando comandos improvisados.
- [ ] Não estou alterando dados.
- [ ] O cliente está claramente identificado.
- [ ] O período está claramente definido.
- [ ] A execução está sujeita à aprovação do ambiente quando aplicável.
- [ ] Sei exatamente qual resultado espero obter.

Se qualquer item crítico não puder ser confirmado:

**PARAR.**

---

# 36. REGRA DE OURO

> **O agente não deve fazer o que consegue fazer.**
>
> **O agente deve fazer somente o que está autorizado a fazer, pelo mecanismo correto, para a finalidade correta.**

