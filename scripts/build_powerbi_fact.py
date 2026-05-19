import sqlite3

import pandas as pd

from calculate_spreads import calculate_market_facts

DB_PATH = "power_market.db"


def validate_fact_table(df: pd.DataFrame) -> None:
    if df.empty:
        raise ValueError("fact_power_market is empty")

    key_nulls = df[["date", "settlement_period"]].isna().sum().sum()
    if key_nulls > 0:
        raise ValueError("fact_power_market contains null keys")

    bad_periods = df[
        (~df["settlement_period"].between(1, 50, inclusive="both"))
        | (df["settlement_period"].isna())
    ]
    if not bad_periods.empty:
        raise ValueError("settlement_period out of valid GB range")

    daily_counts = df.groupby("date")["settlement_period"].nunique()
    short_days = daily_counts[daily_counts < 46]
    if not short_days.empty:
        print("WARNING: Some dates have fewer than 46 settlement periods")
        print(short_days.head())


def main() -> None:
    fact = calculate_market_facts(DB_PATH)
    validate_fact_table(fact)

    with sqlite3.connect(DB_PATH) as conn:
        fact.to_sql("fact_power_market", conn, if_exists="replace", index=False)

    print(f"Loaded {len(fact)} rows into fact_power_market")


if __name__ == "__main__":
    main()
