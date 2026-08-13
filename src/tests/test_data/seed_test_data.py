from db.connection import get_connection
from db.queries.clients import insert_client, get_client_by_slug


def seed():
    existing = get_client_by_slug("cliente-teste")
    if existing:
        client_id = existing["id"]
        print(f"Cliente de teste já existe (id={client_id})")
    else:
        client_id = insert_client("Cliente Teste", "cliente-teste", industry="e-commerce")
        print(f"Cliente criado (id={client_id})")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """INSERT INTO ad_accounts (client_id, platform_id, external_account_id, name)
           VALUES (%s, %s, %s, %s)""",
        (client_id, 1, "123-456-7890", "Conta Google Ads Teste"),
    )
    conn.commit()
    ad_account_id = cursor.lastrowid
    print(f"Conta de anúncio criada (id={ad_account_id})")

    cursor.execute(
        """INSERT INTO campaigns (ad_account_id, external_campaign_id, name, objective, status, budget_type, budget_amount, start_date)
           VALUES (%s, %s, %s, %s, %s, %s, %s, CURDATE())""",
        (ad_account_id, "camp-001", "Campanha de Teste", "conversions", "active", "daily", 100.00),
    )
    conn.commit()
    campaign_id = cursor.lastrowid
    print(f"Campanha criada (id={campaign_id})")

    cursor.execute(
        """INSERT INTO ad_groups (campaign_id, external_ad_group_id, name, status)
           VALUES (%s, %s, %s, %s)""",
        (campaign_id, "adgroup-001", "Conjunto Teste", "active"),
    )
    conn.commit()
    ad_group_id = cursor.lastrowid
    print(f"Conjunto de anúncios criado (id={ad_group_id})")

    cursor.execute(
        """INSERT INTO ads (ad_group_id, external_ad_id, name, format, status)
           VALUES (%s, %s, %s, %s, %s)""",
        (ad_group_id, "ad-001", "Anúncio Teste", "image", "active"),
    )
    conn.commit()
    ad_id = cursor.lastrowid
    print(f"Anúncio criado (id={ad_id})")

    cursor.execute(
        """INSERT INTO daily_metrics (ad_id, metric_date, impressions, clicks, spend, platform_conversions, platform_conversion_value)
           VALUES (%s, CURDATE(), %s, %s, %s, %s, %s)""",
        (ad_id, 1500, 45, 87.50, 3, 270.00),
    )
    conn.commit()
    print("Métrica diária inserida.")

    cursor.close()
    conn.close()
    print("\nSeed concluído com sucesso!")


if __name__ == "__main__":
    seed()