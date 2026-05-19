PRAGMA foreign_keys = OFF;

DROP TABLE IF EXISTS stg_system_prices;
CREATE TABLE stg_system_prices (
    date TEXT NOT NULL,
    settlement_period INTEGER NOT NULL,
    sbp_gbp_mwh REAL,
    ssp_gbp_mwh REAL
);

INSERT INTO stg_system_prices (date, settlement_period, sbp_gbp_mwh, ssp_gbp_mwh)
SELECT
    DATE(settlementDate) AS date,
    CAST(settlementPeriod AS INTEGER) AS settlement_period,
    CAST(systemBuyPrice AS REAL) AS sbp_gbp_mwh,
    CAST(systemSellPrice AS REAL) AS ssp_gbp_mwh
FROM system_prices;

DROP TABLE IF EXISTS stg_fuel_mix;
CREATE TABLE stg_fuel_mix (
    date TEXT NOT NULL,
    settlement_period INTEGER NOT NULL,
    fuel_type TEXT NOT NULL,
    generation_mw REAL
);

INSERT INTO stg_fuel_mix (date, settlement_period, fuel_type, generation_mw)
SELECT
    DATE(settlementDate) AS date,
    CAST(settlementPeriod AS INTEGER) AS settlement_period,
    fuelType AS fuel_type,
    CAST(generation AS REAL) AS generation_mw
FROM fuel_mix;

DROP TABLE IF EXISTS stg_demand_indo;
CREATE TABLE stg_demand_indo (
    date TEXT NOT NULL,
    settlement_period INTEGER NOT NULL,
    demand_mw REAL
);

INSERT INTO stg_demand_indo (date, settlement_period, demand_mw)
SELECT
    DATE(settlementDate) AS date,
    CAST(settlementPeriod AS INTEGER) AS settlement_period,
    CAST(demand AS REAL) AS demand_mw
FROM demand_indo;

DROP TABLE IF EXISTS dim_commodity_prices;
CREATE TABLE dim_commodity_prices (
    date TEXT PRIMARY KEY,
    gas_p_per_therm REAL NOT NULL,
    carbon_eur_per_tco2 REAL NOT NULL,
    eur_gbp REAL NOT NULL DEFAULT 0.86
);

INSERT INTO dim_commodity_prices (date, gas_p_per_therm, carbon_eur_per_tco2, eur_gbp)
SELECT
    DATE(price_date) AS date,
    CAST(gas_p_therm AS REAL) AS gas_p_per_therm,
    CAST(carbon_eur_mwh AS REAL) AS carbon_eur_per_tco2,
    0.86
FROM commodity_prices;
