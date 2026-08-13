import os
from datetime import date

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


def get_daily_campaign_metrics(
    customer_id: str,
    start_date: date,
    end_date: date,
):
    client = create_client()

    google_ads_service = client.get_service("GoogleAdsService")

    query = f"""
        SELECT
            segments.date,
            campaign.id,
            campaign.name,
            campaign.status,
            campaign.advertising_channel_type,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions,
            metrics.ctr,
            metrics.average_cpc,
            metrics.cost_per_conversion
        FROM campaign
        WHERE segments.date BETWEEN
            '{start_date.isoformat()}'
            AND
            '{end_date.isoformat()}'
        ORDER BY
            segments.date,
            campaign.id
    """

    response = google_ads_service.search(
        customer_id=customer_id,
        query=query,
    )

    results = []

    for row in response:
        campaign = row.campaign
        metrics = row.metrics

        results.append(
            {
                "date": row.segments.date,
                "campaign_id": campaign.id,
                "campaign_name": campaign.name,
                "campaign_status": campaign.status.name,
                "channel_type": campaign.advertising_channel_type.name,
                "impressions": metrics.impressions,
                "clicks": metrics.clicks,
                "cost_micros": metrics.cost_micros,
                "cost": metrics.cost_micros / 1_000_000,
                "conversions": metrics.conversions,
                "ctr": metrics.ctr,
                "average_cpc": metrics.average_cpc / 1_000_000,
                "cost_per_conversion": (
                    metrics.cost_per_conversion / 1_000_000
                    if metrics.cost_per_conversion
                    else 0
                ),
            }
        )

    return results