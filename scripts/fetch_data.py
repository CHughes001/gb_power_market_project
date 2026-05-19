import sqlite3
from datetime import datetime

import pandas as pd
import requests

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"
DB_PATH = "power_market.db"


def format_date(date_str: str) -> str:
    return datetime.fromisoformat(date_str).strftime("%Y-%m-%d")


def call_api(url: str, params: dict | None = None) -> dict:
    try:
        response = requests.get(url, params=params or {}, timeout=20)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as exc:
        print(f"HTTP Error {response.status_code}: {url}")
        raise exc
    except requests.exceptions.RequestException as exc:
        print(f"Connection Error: {url}")
        raise exc


def validate_response(data: dict, label: str = "") -> None:
    if "data" not in data:
        raise ValueError(f"Unexpected API response{f' ({label})' if label else ''}: {data}")


def fetch_system_prices(date_from: str, date_to: str) -> pd.DataFrame:
    all_rows = []
    for date in pd.date_range(date_from, date_to):
        date_str = date.strftime("%Y-%m-%d")
        url = f"{BASE_URL}/balancing/settlement/system-prices/{date_str}"
        data = call_api(url, {"format": "json"})
        validate_response(data, label=date_str)
        all_rows.extend(data["data"] or [])

    df = pd.DataFrame(all_rows)
    if df.empty:
        return df

    df = df.rename(
        columns={
            "settlementDate": "date",
            "settlementPeriod": "settlement_period",
            "systemBuyPrice": "sbp_gbp_mwh",
            "systemSellPrice": "ssp_gbp_mwh",
        }
    )
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    df["settlement_period"] = pd.to_numeric(df["settlement_period"], errors="coerce").astype("Int64")
    df["sbp_gbp_mwh"] = pd.to_numeric(df["sbp_gbp_mwh"], errors="coerce")
    df["ssp_gbp_mwh"] = pd.to_numeric(df["ssp_gbp_mwh"], errors="coerce")
    return df[["date", "settlement_period", "sbp_gbp_mwh", "ssp_gbp_mwh"]].dropna(
        subset=["date", "settlement_period"]
    )


def fetch_generation_fuelmix(date_from: str, date_to: str, fuel_type: list | None = None) -> pd.DataFrame:
    all_rows = []
    for date in pd.date_range(date_from, date_to):
        date_str = date.strftime("%Y-%m-%d")
        params = {
            "settlementDateFrom": date_str,
            "settlementDateTo": date_str,
            "format": "json",
        }
        if fuel_type:
            params["fuelType"] = fuel_type

        data = call_api(f"{BASE_URL}/datasets/FUELINST", params)
        validate_response(data, label=f"FUELINST {date_str}")
        all_rows.extend(data["data"] or [])

    df = pd.DataFrame(all_rows)
    if df.empty:
        return df

    df = df.rename(
        columns={
            "settlementDate": "date",
            "settlementPeriod": "settlement_period",
            "fuelType": "fuel_type",
            "generation": "generation_mw",
        }
    )
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    df["settlement_period"] = pd.to_numeric(df["settlement_period"], errors="coerce").astype("Int64")
    df["generation_mw"] = pd.to_numeric(df["generation_mw"], errors="coerce")
    return df[["date", "settlement_period", "fuel_type", "generation_mw"]].dropna(
        subset=["date", "settlement_period", "fuel_type"]
    )


def fetch_demand(date_from: str, date_to: str, dataset: str = "INDO") -> pd.DataFrame:
    all_rows = []
    for date in pd.date_range(date_from, date_to):
        date_str = date.strftime("%Y-%m-%d")
        params = {
            "publishDateTimeFrom": f"{date_str}T00:00:00Z",
            "publishDateTimeTo": f"{date_str}T23:59:59Z",
            "format": "json",
        }
        data = call_api(f"{BASE_URL}/datasets/{dataset}", params)
        validate_response(data, label=f"{dataset} {date_str}")
        all_rows.extend(data["data"] or [])

    df = pd.DataFrame(all_rows)
    if df.empty:
        return df

    df = df.rename(
        columns={
            "settlementDate": "date",
            "settlementPeriod": "settlement_period",
            "demand": "demand_mw",
            "nationalDemand": "demand_mw",
        }
    )
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    df["settlement_period"] = pd.to_numeric(df["settlement_period"], errors="coerce").astype("Int64")
    df["demand_mw"] = pd.to_numeric(df["demand_mw"], errors="coerce")
    return df[["date", "settlement_period", "demand_mw"]].dropna(subset=["date", "settlement_period"])


def save_to_db(df: pd.DataFrame, table: str, db_path: str = DB_PATH, mode: str = "replace") -> None:
    with sqlite3.connect(db_path) as conn:
        df.to_sql(table, conn, if_exists=mode, index=False, method="multi", chunksize=500)
    print(f"Saved {len(df)} rows to '{table}'")


if __name__ == "__main__":
    start_date = format_date("2026-04-01")
    end_date = format_date("2026-04-10")

    print("\n--- FETCH SYSTEM PRICES ---")
    system_prices = fetch_system_prices(start_date, end_date)
    print(system_prices.head())
    print(system_prices.shape)
    save_to_db(system_prices, "stg_system_prices")

    print("\n--- FETCH FUEL MIX ---")
    fuel_mix = fetch_generation_fuelmix(start_date, end_date)
    print(fuel_mix.head())
    print(fuel_mix.shape)
    save_to_db(fuel_mix, "stg_fuel_mix")

    print("\n--- FETCH DEMAND (INDO) ---")
    demand_indo = fetch_demand(start_date, end_date, dataset="INDO")
    print(demand_indo.head())
    print(demand_indo.shape)
    save_to_db(demand_indo, "stg_demand_indo")