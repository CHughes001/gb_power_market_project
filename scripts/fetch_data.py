# fetch_data.py
# Fast BMRS / Elexon data loader using date-range endpoints

import sqlite3
import requests
import pandas as pd
from datetime import datetime

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"
DB_PATH = "power_market.db"


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def format_date(date_str: str) -> str:
    """Validate and return yyyy-MM-dd."""
    return datetime.fromisoformat(date_str).strftime("%Y-%m-%d")


def call_api(url: str, params: dict = None) -> dict:
    """GET request with timeout / error handling."""
    try:
        r = requests.get(url, params=params or {}, timeout=20)
        r.raise_for_status()
        return r.json()

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error {r.status_code}: {url}")
        raise e

    except requests.exceptions.RequestException as e:
        print(f"Connection Error: {url}")
        raise e


def validate_response(data: dict, label: str = ""):
    """Raise clearly if BMRS response is missing expected data key."""
    if "data" not in data:
        raise ValueError(f"Unexpected API response{f' ({label})' if label else ''}:\n{data}")


# --------------------------------------------------
# Fetch Functions
# --------------------------------------------------

def fetch_system_prices(date_from: str, date_to: str) -> pd.DataFrame:
    """
    Fetch system buy/sell prices for a date range.
    One API call per day — each call returns all 48 settlement periods.
    """
    all_rows = []

    for date in pd.date_range(date_from, date_to):
        date_str = date.strftime("%Y-%m-%d")
        url = f"{BASE_URL}/balancing/settlement/system-prices/{date_str}"
        data = call_api(url, {"format": "json"})
        validate_response(data, label=date_str)

        if data["data"]:
            all_rows.extend(data["data"])

    df = pd.DataFrame(all_rows)

    if df.empty:
        print("WARNING: No system price data returned")

    return df


def fetch_generation_fuelmix(
    date_from: str,
    date_to: str,
    fuel_type: list = None
) -> pd.DataFrame:
    """
    Fetch generation by fuel type, looping day by day.
    Uses settlementDateFrom = settlementDateTo (same day) per call,
    which forces the API to filter by that specific date.
    """
    all_rows = []

    for date in pd.date_range(date_from, date_to):
        date_str = date.strftime("%Y-%m-%d")
        url = f"{BASE_URL}/datasets/FUELINST"

        params = {
            "settlementDateFrom": date_str,
            "settlementDateTo":   date_str,  # same date = one day
            "format": "json"
        }

        if fuel_type:
            params["fuelType"] = fuel_type

        data = call_api(url, params)
        validate_response(data, label=f"FUELINST {date_str}")

        if data["data"]:
            all_rows.extend(data["data"])

    df = pd.DataFrame(all_rows)

    if df.empty:
        print("WARNING: No fuel mix data returned")

    return df

def fetch_demand(
    date_from: str,
    date_to: str,
    dataset: str = "INDO"
) -> pd.DataFrame:
    """
    Fetch demand data (INDO) for a date range.
    INDO only supports publishDateTime filters, not settlementDate.
    Loops day by day using publish datetime window.
    """
    all_rows = []

    for date in pd.date_range(date_from, date_to):
        date_str = date.strftime("%Y-%m-%d")
        url = f"{BASE_URL}/datasets/{dataset}"

        params = {
            "publishDateTimeFrom": f"{date_str}T00:00:00Z",
            "publishDateTimeTo":   f"{date_str}T23:59:59Z",
            "format": "json"
        }

        data = call_api(url, params)
        validate_response(data, label=f"{dataset} {date_str}")

        if data["data"]:
            all_rows.extend(data["data"])

    df = pd.DataFrame(all_rows)

    if df.empty:
        print(f"WARNING: No {dataset} data returned")

    return df

# --------------------------------------------------
# Database
# --------------------------------------------------

def save_to_db(
    df: pd.DataFrame,
    table: str,
    db_path: str = DB_PATH,
    mode: str = "replace"
):
    """
    Save DataFrame to SQLite.

    mode:
        replace = overwrite table (default — safe for re-runs)
        append  = add rows without removing existing data
    """
    with sqlite3.connect(db_path) as conn:
        df.to_sql(
            table,
            conn,
            if_exists=mode,
            index=False,
            method="multi",
            chunksize=500
        )

    print(f"Saved {len(df)} rows to '{table}'")


# --------------------------------------------------
# Main
# --------------------------------------------------

if __name__ == "__main__":

    START_DATE = "2026-04-01"
    END_DATE   = "2026-04-10"

    # ---------------- SYSTEM PRICES ----------------
    print("\n--- FETCH SYSTEM PRICES ---")
    df_prices = fetch_system_prices(START_DATE, END_DATE)
    print(df_prices.head())
    print(df_prices.shape)
    save_to_db(df_prices, "system_prices")

    # ---------------- FUEL MIX ----------------
    print("\n--- FETCH FUEL MIX ---")
    df_fuel = fetch_generation_fuelmix(START_DATE, END_DATE)
    print(df_fuel.head())
    print(df_fuel.shape)
    save_to_db(df_fuel, "fuel_mix")

    # Verify correct dates came back
    print("\nFuel mix dates in response:")
    print(df_fuel["settlementDate"].unique())

    # ---------------- DEMAND ----------------
    print("\n--- FETCH DEMAND (INDO) ---")
    df_demand = fetch_demand(START_DATE, END_DATE, dataset="INDO")
    print(df_demand.head())
    print(df_demand.shape)
    save_to_db(df_demand, "demand_indo")

    # Verify correct dates came back
    print("\nDemand dates in response:")
    print(df_demand["settlementDate"].unique())