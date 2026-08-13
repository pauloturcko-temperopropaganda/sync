import os

from dotenv import load_dotenv
from google.ads.googleads.client import GoogleAdsClient


load_dotenv(".env.admin")


def main():
    config = {
        "developer_token": os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
        "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"],
        "refresh_token": os.environ["GOOGLE_ADS_REFRESH_TOKEN"],
        "use_proto_plus": True,
    }

    client = GoogleAdsClient.load_from_dict(config)

    customer_service = client.get_service("CustomerService")

    accessible_customers = (
        customer_service.list_accessible_customers()
    )

    print("\nContas acessíveis:")
    print("=" * 60)

    for resource_name in accessible_customers.resource_names:
        customer_id = resource_name.split("/")[-1]
        print(customer_id)

    print("=" * 60)


if __name__ == "__main__":
    main()