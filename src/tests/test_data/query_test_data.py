from db.connection import get_connection


def get_campaign_performance():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT
            c.name AS client_name,
            camp.name AS campaign_name,
            SUM(dm.impressions) AS total_impressions,
            SUM(dm.clicks) AS total_clicks,
            SUM(dm.spend) AS total_spend,
            SUM(dm.platform_conversions) AS total_conversions
        FROM clients c
        JOIN ad_accounts aa ON aa.client_id = c.id
        JOIN campaigns camp ON camp.ad_account_id = aa.id
        JOIN ad_groups ag ON ag.campaign_id = camp.id
        JOIN ads a ON a.ad_group_id = ag.id
        JOIN daily_metrics dm ON dm.ad_id = a.id
        GROUP BY c.id, camp.id
        """
    )
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results


if __name__ == "__main__":
    for row in get_campaign_performance():
        print(row)