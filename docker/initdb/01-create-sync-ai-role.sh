#!/bin/bash
# Executado automaticamente pelo entrypoint oficial do Postgres,
# apenas na primeira inicialização do volume de dados.
#
# Cria o papel somente-leitura usado pelas ferramentas de IA
# (src/ai_tools/db.py, autenticado via .env.agent).
set -euo pipefail

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE ROLE sync_ai WITH LOGIN PASSWORD '$SYNC_AI_PASSWORD';

    GRANT CONNECT ON DATABASE $POSTGRES_DB TO sync_ai;
    GRANT USAGE ON SCHEMA public TO sync_ai;

    -- Tabelas que já existirem no momento em que este script rodar.
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO sync_ai;

    -- Tabelas criadas por migrations FUTURAS também ficam visíveis
    -- ao sync_ai automaticamente, sem precisar de GRANT manual a
    -- cada nova migration.
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO sync_ai;
EOSQL
