import sqlite3
import pandas as pd

# Constants 
CCGT_HEAT_RATE    = 7.0    # GJ per MWh electricity output
EUR_GBP           = 0.86   # update periodically
EMISSIONS_FACTOR = 0.2  # tCO₂/MWh — standard CCGT figure used in GB spread analysis

# Therm → GJ conversion (needed for your gas_p_therm input)
THERM_TO_GJ = 0.105505585  # 1 therm = 0.1055 GJ
DEBUG = False #TRUE for extra printouts during development

def calculate_spreads(db_path="power_market.db") -> pd.DataFrame:
    with sqlite3.connect(db_path) as conn:
        prices = pd.read_sql("SELECT * FROM system_prices", conn)
        comms  = pd.read_sql("SELECT * FROM commodity_prices", conn)

    prices["date"] = pd.to_datetime(prices["settlementDate"]).dt.strftime("%Y-%m-%d")
    comms["date"]  = pd.to_datetime(comms["price_date"]).dt.strftime("%Y-%m-%d")

    df = prices.merge(comms, on="date", how="left")

    if DEBUG:
        print("Total rows:", len(df))
        print("Missing gas:", df["gas_p_therm"].isna().sum())
        print("Missing carbon:", df["carbon_eur_mwh"].isna().sum())

    # -----------------------------
    # GAS: pence/therm → £/GJ
    # -----------------------------
    df["gas_gbp_therm"] = df["gas_p_therm"] / 100
    df["gas_gbp_gj"] = df["gas_gbp_therm"] / THERM_TO_GJ

    # -----------------------------
    # Spark Spread
    # -----------------------------
    df["spark_spread"] = df["systemBuyPrice"] - df["gas_gbp_gj"] * CCGT_HEAT_RATE

    # -----------------------------
    # Carbon cost
    # -----------------------------
    df["carbon_gbp_mwh"] = df["carbon_eur_mwh"] * EUR_GBP * EMISSIONS_FACTOR

    # -----------------------------
    # Clean Spark Spread
    # -----------------------------
    df["clean_spark_spread"] = df["spark_spread"] - df["carbon_gbp_mwh"]

    return df



if __name__ == "__main__":
    df = calculate_spreads()

    print(df[[
        "date",
        "settlementPeriod",
        "systemBuyPrice",
        "spark_spread",
        "clean_spark_spread"
    ]].tail(10))

    with sqlite3.connect("power_market.db") as conn:
        df.to_sql("spreads", conn, if_exists="replace", index=False)
