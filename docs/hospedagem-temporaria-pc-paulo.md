# Hospedagem temporária no PC do Paulo — o que foi feito e o que desfazer

**Contexto:** enquanto o acesso da agência inteira a um servidor de verdade
está parado (ver `[[sync_roadmap_ideas]]` na memória do Claude — depende de
alguém liberar acesso ao servidor interno `192.168.1.10`), decidimos em
2026-09-08 usar o próprio PC do Paulo como host temporário: o painel do
Sync (dashboard) e o Postgres continuam rodando só aqui, e o resto da
equipe acessa pela rede local via IP, sem precisar instalar o projeto na
máquina de cada um.

Isso significa que **este PC precisa ficar ligado** pra quem mais usa o
painel conseguir acessar. Quando a agência migrar pra um servidor de
verdade, as mudanças abaixo (feitas especificamente por causa dessa
hospedagem temporária) devem ser desfeitas nesta máquina — o Postgres em
si (dado real dos clientes) precisa ser migrado pro servidor novo antes
de desligar qualquer coisa aqui, isso não é só "desfazer configuração".

## O que foi mudado nesta máquina (Windows + WSL)

### 1. `src/dashboard/app.py` — dashboard escutando na rede, não só localhost
Trocado `host="127.0.0.1"` por `host="0.0.0.0"` no `uvicorn.run()`, pra
outros PCs da rede conseguirem acessar via `http://192.168.1.82:8050`
(o `.82` é o IP deste PC na rede local — pode mudar se o roteador
reatribuir IP, já que não foi configurado IP fixo).

**Ao migrar pra servidor:** não precisa reverter — um servidor de verdade
também vai querer escutar em `0.0.0.0` (ou no IP dele). É só o arquivo
`app.py` migrar junto com o resto do projeto.

### 2. Regra de firewall do Windows — porta 8050 liberada na rede
Criada uma regra de entrada (`New-NetFirewallRule -DisplayName "Sync
Dashboard" -LocalPort 8050 -Profile Private`) liberando a porta 8050 pra
rede Privada.

**Ao migrar pra servidor:** remover essa regra deste PC (ela não faz mais
sentido aqui). No servidor novo vai precisar de uma regra equivalente lá.

### 3. Tarefa agendada "Sync - Dashboard" (nova)
Criada pra subir o painel sozinho ao ligar o PC, sem precisar abrir
PyCharm nem terminal manualmente — roda `scripts\start_dashboard.bat` no
boot, modo S4U (não depende de tela desbloqueada), reinicia sozinha até
3x se cair, sem limite de tempo de execução.

**Ao migrar pra servidor:** **excluir esta tarefa deste PC**
(`Unregister-ScheduledTask -TaskName "Sync - Dashboard"`). O servidor novo
vai ter seu próprio jeito de manter o serviço no ar (systemd, Docker,
supervisor etc. — não necessariamente Task Scheduler do Windows).

### 4. Tarefa agendada "Sync - WSL Ubuntu" (nova)
Criada pra ligar o WSL (distro Ubuntu) automaticamente no boot do
Windows — sem isso, o Postgres (que roda em Docker dentro do WSL) fica
"dormindo" até alguém abrir um terminal WSL manualmente. Dentro do
Ubuntu, o `docker.service` já está habilitado via systemd e o container
`sync_postgres` tem `restart: unless-stopped`, então só precisa acordar o
WSL — o resto sobe sozinho.

**Ao migrar pra servidor:** **excluir esta tarefa deste PC**
(`Unregister-ScheduledTask -TaskName "Sync - WSL Ubuntu"`). O Postgres do
servidor novo não vai depender de WSL nenhum.

### 5. Tarefa agendada "Sync - Meta Ads Diario" (já existia — só ajustada)
Essa tarefa já existia antes de hoje (sincronização diária às 8h). O que
mudou foi só o **tipo de logon**, de "Interactive only" pra **S4U** — ela
estava falhando toda vez que a tela ficava travada de madrugada (era o
motivo original de o sync não estar rodando sozinho). Essa correção **não
tem nada a ver com a hospedagem temporária** — é uma correção de bug de
verdade, permanente, que continua fazendo sentido mesmo depois de migrar
pra servidor (qualquer agendador de tarefas do Windows teria o mesmo
problema com sessão travada).

**Ao migrar pra servidor:** não desfazer — mas se o sync passar a rodar
via cron/systemd no servidor novo em vez de Task Scheduler do Windows,
essa tarefa toda (não só o logon type) deixa de ser necessária aqui.

## Resumo rápido — checklist pra quando migrar

- [ ] Migrar o dado do Postgres (`sync_postgres_data`, volume Docker) pro
      servidor novo — **isso vem antes de qualquer outra coisa**.
- [ ] Excluir a tarefa agendada "Sync - Dashboard" deste PC.
- [ ] Excluir a tarefa agendada "Sync - WSL Ubuntu" deste PC.
- [ ] Remover a regra de firewall "Sync Dashboard" (porta 8050) deste PC.
- [ ] Decidir se a tarefa "Sync - Meta Ads Diario" continua aqui ou vira
      cron/systemd no servidor novo — mas o ajuste de logon (S4U) em si
      não precisa ser desfeito, é uma correção válida independente de onde
      rodar.
- [ ] Conferir se o `.env.admin` / credenciais do Meta precisam ser
      recriadas no servidor novo ou só copiadas (cuidado ao copiar segredo
      entre máquinas).
