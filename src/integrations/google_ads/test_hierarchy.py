import os
from collections import deque

from dotenv import load_dotenv
from google.ads.googleads.client import GoogleAdsClient


load_dotenv(".env.admin")


def create_client():
    config = {
        "developer_token": os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
        "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"],
        "refresh_token": os.environ["GOOGLE_ADS_REFRESH_TOKEN"],
        "login_customer_id": os.environ["GOOGLE_ADS_LOGIN_CUSTOMER_ID"],
        "use_proto_plus": True,
    }

    return GoogleAdsClient.load_from_dict(config)


def main():
    client = create_client()

    google_ads_service = client.get_service("GoogleAdsService")

    manager_id = os.environ["GOOGLE_ADS_LOGIN_CUSTOMER_ID"]

    query = """
        SELECT
            customer_client.client_customer,
            customer_client.level,
            customer_client.manager,
            customer_client.descriptive_name,
            customer_client.currency_code,
            customer_client.time_zone,
            customer_client.id
        FROM customer_client
        WHERE customer_client.level <= 1
    """

    queue = deque([manager_id])
    visited = set()

    print()
    print("=" * 80)
    print("HIERARQUIA GOOGLE ADS")
    print("=" * 80)

    while queue:
        customer_id = queue.popleft()

        if customer_id in visited:
            continue

        visited.add(customer_id)

        print()
        print(f"Consultando conta: {customer_id}")

        response = google_ads_service.search(
            customer_id=customer_id,
            query=query,
        )

        for row in response:
            customer = row.customer_client

            indent = "  " * customer.level

            account_type = "GERENTE" if customer.manager else "CLIENTE"

            print(
                f"{indent}- {customer.id} | "
                f"{customer.descriptive_name} | "
                f"{account_type} | "
                f"{customer.currency_code} | "
                f"{customer.time_zone}"
            )

            if customer.manager and customer.id != int(customer_id):
                queue.append(str(customer.id))

    print()
    print("=" * 80)
    print("FIM")
    print("=" * 80)


if __name__ == "__main__":
    main()