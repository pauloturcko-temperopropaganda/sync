import os

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

    customer_id = "4378571170"

    google_ads_service = client.get_service("GoogleAdsService")

    query = """
        SELECT
            campaign.id,
            campaign.name,
            campaign.status,
            campaign.advertising_channel_type
        FROM campaign
        ORDER BY campaign.id
    """

    response = google_ads_service.search(
        customer_id=customer_id,
        query=query,
    )

    print()
    print("=" * 100)
    print(f"CAMPANHAS DA CONTA {customer_id}")
    print("=" * 100)

    for row in response:
        campaign = row.campaign

        print(
            f"ID: {campaign.id} | "
            f"Nome: {campaign.name} | "
            f"Status: {campaign.status.name} | "
            f"Tipo: {campaign.advertising_channel_type.name}"
        )

    print("=" * 100)


if __name__ == "__main__":
    main()