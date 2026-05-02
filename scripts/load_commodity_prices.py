"""
load_commodity_prices.py

Ingests gas and carbon price CSVs, cleans them, normalises column names,
merges them on price_date, and loads into SQLite as commodity_prices.

Final schema:
    price_date (YYYY-MM-DD)
    gas_p_therm
    carbon_eur_mwh
"""

import pandas as pd
import sqlite3
import sys


# -----------------------------
# 1. Load & clean gas prices
# -----------------------------
def load_gas_prices(path: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(path, parse_dates=["Date"])
    except Exception as e:
        print(f"ERROR: Failed to load gas CSV: {e}")
        sys.exit(1)

    # Clean column names
    df.columns = df.columns.str.strip()

    print("Gas columns:", df.columns)
    print(df.head())

    # Rename
    df = df.rename(columns={
        "Date": "price_date",
        "Price": "gas_p_therm"
    })

    # 🔥 Ensure numeric (CRITICAL)
    df["gas_p_therm"] = (
        df["gas_p_therm"]
        .astype(str)
        .str.replace(",", "", regex=False)
    )
    df["gas_p_therm"] = pd.to_numeric(df["gas_p_therm"], errors="coerce")

    # Format date properly
    df["price_date"] = pd.to_datetime(df["price_date"]).dt.date.astype(str)

    # Aggregate to daily (safe even if already daily)
    df = df.groupby("price_date", as_index=False)["gas_p_therm"].mean()

    # Validate
    if df["gas_p_therm"].isna().all():
        raise ValueError("Gas prices failed to load — column is entirely NULL")

    return df


# -----------------------------
# 2. Load & clean carbon prices
# -----------------------------
def load_carbon_prices(path: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(path, parse_dates=["Date"])
    except Exception as e:
        print(f"ERROR: Failed to load carbon CSV: {e}")
        sys.exit(1)

    df.columns = df.columns.str.strip()

    # Rename
    df = df.rename(columns={
        "Date": "price_date",
        "Price (EUR/MWhe)": "carbon_eur_mwh"
    })

    # Ensure numeric
    df["carbon_eur_mwh"] = pd.to_numeric(df["carbon_eur_mwh"], errors="coerce")

    # Format date
    df["price_date"] = pd.to_datetime(df["price_date"]).dt.date.astype(str)

    # 🔥 CRITICAL: aggregate to ONE value per day
    df = df.groupby("price_date", as_index=False)["carbon_eur_mwh"].mean()

    # Validate
    if df["carbon_eur_mwh"].isna().all():
        raise ValueError("Carbon prices failed to load — column is entirely NULL")

    return df


# -----------------------------
# 3. Merge & load into SQLite
# -----------------------------
def load_into_sqlite(gas_df: pd.DataFrame, carbon_df: pd.DataFrame, db_path: str):

    merged = gas_df.merge(carbon_df, on="price_date", how="outer")

    # 🔥 CRITICAL: sort BEFORE filling
    merged = merged.sort_values("price_date")

    # Forward + backward fill (handles edges)
    merged["gas_p_therm"] = merged["gas_p_therm"].ffill().bfill()
    merged["carbon_eur_mwh"] = merged["carbon_eur_mwh"].ffill().bfill()

    # Debug
    print("\n--- MERGED SAMPLE ---")
    print(merged.head(10))
    print(merged.tail(10))

    print("\nGas nulls after merge:", merged["gas_p_therm"].isna().sum())
    print("Carbon nulls after merge:", merged["carbon_eur_mwh"].isna().sum())

    # 🔥 HARD FAIL if still broken
    if merged["gas_p_therm"].isna().any():
        raise ValueError("Gas still contains NULLs after merge — check date coverage")

    if merged.empty:
        print("ERROR: Merge produced zero rows. Check date alignment.")
        sys.exit(1)

    with sqlite3.connect(db_path) as conn:
        merged.to_sql("commodity_prices", conn, if_exists="replace", index=False)

    print(f"\nSUCCESS: Loaded {len(merged)} rows into commodity_prices")


# -----------------------------
# 4. Main execution
# -----------------------------
if __name__ == "__main__":
    GAS_PATH = "data/gas_prices.csv"
    CARBON_PATH = "data/carbon_prices.csv"
    DB_PATH = "power_market.db"

    gas_df = load_gas_prices(GAS_PATH)
    carbon_df = load_carbon_prices(CARBON_PATH)

    load_into_sqlite(gas_df, carbon_df, DB_PATH)