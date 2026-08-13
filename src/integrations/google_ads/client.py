import os

from dotenv import load_dotenv
from google.ads.googleads.client import GoogleAdsClient


load_dotenv(".env.admin")


def create_google_ads_client():
    config = {
        "developer_token": os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
        "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"],
        "refresh_token": os.environ["GOOGLE_ADS_REFRESH_TOKEN"],
        "login_customer_id": os.environ["GOOGLE_ADS_LOGIN_CUSTOMER_ID"],
        "use_proto_plus": True,
    }

    return GoogleAdsClient.load_from_dict(config)


def get_geo_metrics():
    client = create_google_ads_client()

    customer_id = os.environ["GOOGLE_ADS_CUSTOMER_ID"]

    ga_service = client.get_service("GoogleAdsService")

    query = """
        SELECT
            campaign.id,
            campaign.name,

            segments.date,

            geographic_view.country_criterion_id,

            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.ctr,
            metrics.average_cpc,
            metrics.conversions,
            metrics.conversions_value,
            metrics.all_conversions,
            metrics.all_conversions_value

        FROM geographic_view

        WHERE
            campaign.id = 22682629376
            AND segments.date BETWEEN '2026-01-26' AND '2026-02-01'

        ORDER BY
            segments.date,
            geographic_view.country_criterion_id
    """

    response = ga_service.search_stream(
        customer_id=customer_id,
        query=query,
    )

    for batch in response:
        for row in batch.results:
            print(
                f"Data: {row.segments.date}\n"
                f"Campanha: {row.campaign.name}\n"
                f"Campanha ID: {row.campaign.id}\n"
                f"Country Criterion ID: "
                f"{row.geographic_view.country_criterion_id}\n"
                f"Impressões: {row.metrics.impressions}\n"
                f"Cliques: {row.metrics.clicks}\n"
                f"Custo (micros): {row.metrics.cost_micros}\n"
                f"CTR: {row.metrics.ctr}\n"
                f"CPC médio (micros): {row.metrics.average_cpc}\n"
                f"Conversões: {row.metrics.conversions}\n"
                f"Valor das conversões: "
                f"{row.metrics.conversions_value}\n"
                f"Todas as conversões: "
                f"{row.metrics.all_conversions}\n"
                f"Valor de todas as conversões: "
                f"{row.metrics.all_conversions_value}\n"
                "-----------------------------"
            )


if __name__ == "__main__":
    get_geo_metrics()