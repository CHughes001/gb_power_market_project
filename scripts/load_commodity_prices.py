import pandas as pd
import sqlite3
import sys


def load_gas_prices(path: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(path, parse_dates=["Date"])
    except Exception as e:
        print(f"ERROR: Failed to load gas CSV: {e}")
        sys.exit(1)

    df.columns = df.columns.str.strip()
    df = df.rename(columns={
        "Date": "date",
        "Price": "gas_p_per_therm"
    })

    df["gas_p_per_therm"] = (
        df["gas_p_per_therm"]
        .astype(str)
        .str.replace(",", "", regex=False)
    )
    df["gas_p_per_therm"] = pd.to_numeric(df["gas_p_per_therm"], errors="coerce")

    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    df = df.groupby("date", as_index=False)["gas_p_per_therm"].mean()

    if df["gas_p_per_therm"].isna().all():
        raise ValueError("Gas prices failed to load — column is entirely NULL")

    return df


def load_carbon_prices(path: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(path, parse_dates=["Date"])
    except Exception as e:
        print(f"ERROR: Failed to load carbon CSV: {e}")
        sys.exit(1)

    df.columns = df.columns.str.strip()

    value_col = None
    for candidate in ["Price (EUR/t)", "Price (EUR/tonne)", "Price (EUR/MWhe)", "Price"]:
        if candidate in df.columns:
            value_col = candidate
            break
    if value_col is None:
        raise ValueError("Carbon CSV missing expected price column")

    df = df.rename(columns={"Date": "date", value_col: "carbon_eur_per_tco2"})
    df["carbon_eur_per_tco2"] = pd.to_numeric(df["carbon_eur_per_tco2"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    df = df.groupby("date", as_index=False)["carbon_eur_per_tco2"].mean()

    if df["carbon_eur_per_tco2"].isna().all():
        raise ValueError("Carbon prices failed to load — column is entirely NULL")

    return df


def load_into_sqlite(gas_df: pd.DataFrame, carbon_df: pd.DataFrame, db_path: str):
    merged = gas_df.merge(carbon_df, on="date", how="outer").sort_values("date")
    merged["gas_p_per_therm"] = merged["gas_p_per_therm"].ffill().bfill()
    merged["carbon_eur_per_tco2"] = merged["carbon_eur_per_tco2"].ffill().bfill()
    merged["eur_gbp"] = 0.86

    if merged["gas_p_per_therm"].isna().any():
        raise ValueError("Gas still contains NULLs after merge — check date coverage")
    if merged["carbon_eur_per_tco2"].isna().any():
        raise ValueError("Carbon still contains NULLs after merge — check date coverage")

    if merged.empty:
        print("ERROR: Merge produced zero rows. Check date alignment.")
        sys.exit(1)

    with sqlite3.connect(db_path) as conn:
        merged.to_sql("dim_commodity_prices", conn, if_exists="replace", index=False)

    print(f"\nSUCCESS: Loaded {len(merged)} rows into dim_commodity_prices")


if __name__ == "__main__":
    GAS_PATH = "data/gas_prices.csv"
    CARBON_PATH = "data/carbon_prices.csv"
    DB_PATH = "power_market.db"

    gas_df = load_gas_prices(GAS_PATH)
    carbon_df = load_carbon_prices(CARBON_PATH)

    load_into_sqlite(gas_df, carbon_df, DB_PATH)