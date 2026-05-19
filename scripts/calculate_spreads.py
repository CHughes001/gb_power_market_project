import sqlite3

import pandas as pd

THERM_TO_MWH = 0.0293071
CCGT_HEAT_RATE_MWH_TH_PER_MWH_E = 1.9
EMISSIONS_FACTOR_TCO2_PER_MWH = 0.36
DEFAULT_EUR_GBP = 0.86
DEBUG = False


def _compute_wind_share(fuel_mix: pd.DataFrame) -> pd.DataFrame:
    if fuel_mix.empty:
        return pd.DataFrame(columns=["date", "settlement_period", "wind_pct"])

    agg = fuel_mix.groupby(["date", "settlement_period"], as_index=False).agg(
        total_generation_mw=("generation_mw", "sum")
    )
    wind = (
        fuel_mix[fuel_mix["fuel_type"].str.upper() == "WIND"]
        .groupby(["date", "settlement_period"], as_index=False)
        .agg(wind_generation_mw=("generation_mw", "sum"))
    )
    out = agg.merge(wind, on=["date", "settlement_period"], how="left")
    out["wind_generation_mw"] = out["wind_generation_mw"].fillna(0.0)
    out["wind_pct"] = (out["wind_generation_mw"] * 100.0) / out["total_generation_mw"].replace(0, pd.NA)
    return out[["date", "settlement_period", "wind_pct"]]


def calculate_market_facts(db_path: str = "power_market.db") -> pd.DataFrame:
    with sqlite3.connect(db_path) as conn:
        prices = pd.read_sql("SELECT * FROM stg_system_prices", conn)
        comms = pd.read_sql("SELECT * FROM dim_commodity_prices", conn)
        fuel_mix = pd.read_sql("SELECT * FROM stg_fuel_mix", conn)

    prices["date"] = pd.to_datetime(prices["date"]).dt.strftime("%Y-%m-%d")
    prices["settlement_period"] = pd.to_numeric(prices["settlement_period"], errors="coerce").astype("Int64")
    comms["date"] = pd.to_datetime(comms["date"]).dt.strftime("%Y-%m-%d")

    wind_share = _compute_wind_share(fuel_mix)
    wind_share["settlement_period"] = pd.to_numeric(
        wind_share["settlement_period"], errors="coerce"
    ).astype("Int64")

    df = prices.merge(comms, on="date", how="left").merge(
        wind_share, on=["date", "settlement_period"], how="left"
    )

    df["gas_gbp_per_therm"] = pd.to_numeric(df["gas_p_per_therm"], errors="coerce") / 100.0
    df["gas_gbp_mwh"] = df["gas_gbp_per_therm"] / THERM_TO_MWH
    df["eur_gbp"] = pd.to_numeric(df["eur_gbp"], errors="coerce").fillna(DEFAULT_EUR_GBP)

    df["carbon_gbp_mwh"] = (
        pd.to_numeric(df["carbon_eur_per_tco2"], errors="coerce")
        * df["eur_gbp"]
        * EMISSIONS_FACTOR_TCO2_PER_MWH
    )
    df["spark_spread_gbp_mwh"] = (
        pd.to_numeric(df["sbp_gbp_mwh"], errors="coerce")
        - df["gas_gbp_mwh"] * CCGT_HEAT_RATE_MWH_TH_PER_MWH_E
    )
    df["clean_spark_spread_gbp_mwh"] = df["spark_spread_gbp_mwh"] - df["carbon_gbp_mwh"]

    if DEBUG:
        print("Total rows:", len(df))
        print("Missing gas:", df["gas_p_per_therm"].isna().sum())
        print("Missing carbon:", df["carbon_eur_per_tco2"].isna().sum())

    return df[
        [
            "date",
            "settlement_period",
            "sbp_gbp_mwh",
            "ssp_gbp_mwh",
            "wind_pct",
            "gas_gbp_mwh",
            "carbon_gbp_mwh",
            "spark_spread_gbp_mwh",
            "clean_spark_spread_gbp_mwh",
        ]
    ].dropna(subset=["date", "settlement_period"]).sort_values(["date", "settlement_period"])


if __name__ == "__main__":
    df = calculate_market_facts()
    print(
        df[
            [
                "date",
                "settlement_period",
                "sbp_gbp_mwh",
                "spark_spread_gbp_mwh",
                "clean_spark_spread_gbp_mwh",
            ]
        ].tail(10)
    )
    with sqlite3.connect("power_market.db") as conn:
        df.to_sql("fact_power_market", conn, if_exists="replace", index=False)
