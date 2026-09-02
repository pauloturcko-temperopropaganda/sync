"""Mapeamento das contas de anúncio do Meta que o Sync sincroniza.

Vincular uma conta de anúncio a um cliente/organização é uma decisão
de negócio (qual conta pertence a qual cliente da agência, com qual
slug — idealmente batendo com a pasta correspondente no Vault) — não
é algo que o script de sincronização deva inferir sozinho a partir
do nome da conta na Meta. Por isso fica explícito aqui, não
descoberto automaticamente via API.

Para adicionar uma conta nova:
1. Colocar o ID da conta (formato "act_...") numa variável em
   .env.admin, seguindo o padrão META_AD_ACCOUNT_ID_<NOME>.
2. Adicionar uma entrada abaixo apontando pra essa variável.
3. Atribuir a conta ao System User "Sync API" no Business Manager
   (Contas de anúncio -> Atribuir usuários do sistema -> "Ver
   desempenho"), senão a API retorna erro de permissão.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from src.integrations.meta_ads.client import PROJECT_ROOT, normalize_account_id

load_dotenv(PROJECT_ROOT / ".env.admin")


@dataclass(frozen=True)
class AccountConfig:
    env_var: str
    organization_slug: str
    organization_name: str
    client_slug: str
    client_name: str
    client_industry: str | None = None

    @property
    def external_account_id(self) -> str:
        raw = os.getenv(self.env_var)
        if not raw:
            raise RuntimeError(
                f"Variável de ambiente obrigatória não configurada: {self.env_var}"
            )
        return normalize_account_id(raw)


# client_slug segue a convenção de bater com a pasta em
# vault/Sync/clientes/<slug> quando o cliente já existir lá.
ACCOUNTS: list[AccountConfig] = [
    AccountConfig(
        env_var="META_AD_ACCOUNT_ID_HOSPITAL_DE_OLHOS",
        organization_slug="hospital-de-olhos-videira",
        organization_name="Hospital de Olhos Videira",
        client_slug="hospital-de-olhos-videira",
        client_name="Hospital de Olhos Videira",
        client_industry="Saúde / Oftalmologia",
    ),
    AccountConfig(
        env_var="META_AD_ACCOUNT_ID_CUORE_GYM",
        organization_slug="cuore-gym-fitness",
        organization_name="Cuore Gym & Fitness",
        client_slug="cuore-gym-fitness",
        client_name="Cuore Gym & Fitness",
        client_industry="Academia e Fitness",
    ),
    AccountConfig(
        env_var="META_AD_ACCOUNT_ID_FAZENDA_SONHO_E_REALIDADE",
        organization_slug="fazenda-sonho-e-realidade",
        organization_name="Fazenda Sonho e Realidade",
        client_slug="fazenda-sonho-e-realidade",
        client_name="Fazenda Sonho e Realidade",
        client_industry=None,
    ),
    AccountConfig(
        env_var="META_AD_ACCOUNT_ID_HERDINA_ASSESSORIA_CONTABIL",
        organization_slug="herdina-assessoria-contabil",
        organization_name="Herdina Assessoria Contábil",
        client_slug="herdina-assessoria-contabil",
        client_name="Herdina Assessoria Contábil",
        client_industry="Contabilidade",
    ),
    AccountConfig(
        env_var="META_AD_ACCOUNT_ID_HERDINA_E_LANGARO",
        organization_slug="herdina-e-langaro",
        organization_name="Herdina & Langaro",
        client_slug="herdina-e-langaro",
        client_name="Herdina & Langaro",
        client_industry=None,
    ),
    AccountConfig(
        env_var="META_AD_ACCOUNT_ID_PERFECT_PVC",
        organization_slug="perfect-pvc",
        organization_name="Perfect PVC",
        client_slug="perfect-pvc",
        client_name="Perfect PVC",
        client_industry=None,
    ),
    AccountConfig(
        env_var="META_AD_ACCOUNT_ID_PLADISA",
        organization_slug="pladisa",
        organization_name="Pladisa Planos de Saúde",
        client_slug="pladisa",
        client_name="Pladisa Planos de Saúde",
        client_industry="Saúde / Plano de Saúde",
    ),
    AccountConfig(
        env_var="META_AD_ACCOUNT_ID_VIDEFRIGO",
        organization_slug="videfrigo",
        organization_name="Videfrigo Implementos",
        client_slug="videfrigo",
        client_name="Videfrigo Implementos",
        client_industry="Implementos Agrícolas",
    ),
    AccountConfig(
        env_var="META_AD_ACCOUNT_ID_VIDEMANG",
        organization_slug="videmang",
        organization_name="Videmang",
        client_slug="videmang",
        client_name="Videmang",
        client_industry=None,
    ),
    AccountConfig(
        env_var="META_AD_ACCOUNT_ID_VT_ENGENHARIA",
        organization_slug="vt-engenharia",
        organization_name="VT Engenharia",
        client_slug="vt-engenharia",
        client_name="VT Engenharia",
        client_industry="Engenharia",
    ),
    AccountConfig(
        env_var="META_AD_ACCOUNT_ID_ZORNITTA",
        organization_slug="zornitta",
        organization_name="Super Zornitta",
        client_slug="zornitta",
        client_name="Super Zornitta",
        client_industry="Supermercado",
    ),
    AccountConfig(
        env_var="META_AD_ACCOUNT_ID_WELTER",
        organization_slug="welter",
        organization_name="Welter Alimentos",
        client_slug="welter",
        client_name="Welter Alimentos",
        client_industry="Alimentos",
    ),
    AccountConfig(
        env_var="META_AD_ACCOUNT_ID_MAXXCOLORS",
        organization_slug="maxxcolors",
        organization_name="Maxxcolors Videira",
        client_slug="maxxcolors",
        client_name="Maxxcolors Videira",
        client_industry=None,
    ),
]

# Aproest e Bom Preço foram contas de teste/
# exploração (não são clientes reais da agência) — removidas em
# 2026-09-02.
#
# Nomes/indústrias acima em boa parte são um chute direto do nome da
# variável de ambiente — não tenho como confirmar o nome comercial
# exato nem o segmento de cada uma. Vale conferir e corrigir.

# Aproest e Bom Preço foram contas de teste/exploração (não são
# clientes reais da agência) — removidas em 2026-09-02 na limpeza
# antes de começar a testar relatório com cliente real de verdade.
