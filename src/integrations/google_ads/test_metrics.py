from datetime import date

from metrics import get_daily_campaign_metrics


CUSTOMER_ID = "4378571170"  # ALTERE PARA O ID DA CONTA QUE VOCÊ QUER TESTAR


START_DATE = date(2026, 1, 12)
END_DATE = date(2026, 6, 15)


def main():
    print()
    print("=" * 120)
    print(f"MÉTRICAS GOOGLE ADS - CONTA {CUSTOMER_ID}")
    print(f"PERÍODO: {START_DATE} ATÉ {END_DATE}")
    print("=" * 120)

    results = get_daily_campaign_metrics(
        customer_id=CUSTOMER_ID,
        start_date=START_DATE,
        end_date=END_DATE,
    )

    print(f"\nTotal de registros retornados: {len(results)}\n")

    for row in results:
        print(
            f"{row['date']} | "
            f"{row['campaign_id']} | "
            f"{row['campaign_name']} | "
            f"Impr: {row['impressions']} | "
            f"Cliques: {row['clicks']} | "
            f"Custo: R$ {row['cost']:.2f} | "
            f"Conv: {row['conversions']:.2f} | "
            f"CTR: {row['ctr']:.2%}"
        )

    print()
    print("=" * 120)


if __name__ == "__main__":
    main()