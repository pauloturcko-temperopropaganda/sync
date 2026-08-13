# Sync — AI Safety Rule

Esta é uma regra de segurança do workspace.

## REGRA SEMPRE ATIVA

Antes de executar qualquer ação relacionada ao projeto Sync:

1. Leia `AI_GUIDE.md` na raiz do projeto.
2. Siga integralmente suas regras.
3. Se `AI_GUIDE.md` não puder ser lido, NÃO execute comandos, scripts ou consultas.
4. Não acesse o MariaDB diretamente.
5. Não execute SQL diretamente.
6. Não leia `.env`, credenciais, tokens ou secrets.
7. Não altere dados do MariaDB nesta fase.
8. Só execute ferramentas Python explicitamente listadas como ATIVAS no `AI_GUIDE.md`.
9. Se não existir ferramenta adequada, pare e informe o usuário.
10. Não crie uma ferramenta ou altere código apenas para contornar uma restrição.
11. Não execute comandos destrutivos ou administrativos.
12. Não instale dependências sem solicitação/autorização do usuário.

## IMPORTANTE

`AI_GUIDE.md` é a documentação operacional do Sync.
Esta Rule existe para fazer o Antigravity aplicar essa política como regra persistente do workspace.

Antes de qualquer execução, carregue também o conteúdo de:

`@../../AI_GUIDE.md`
