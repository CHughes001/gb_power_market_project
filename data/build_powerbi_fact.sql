DROP TABLE IF EXISTS fact_power_market;

CREATE TABLE fact_power_market AS
WITH fuel_by_sp AS (
    SELECT
        date,
        settlement_period,
        SUM(generation_mw) AS total_generation_mw,
        SUM(CASE WHEN UPPER(fuel_type) = 'WIND' THEN generation_mw ELSE 0 END) AS wind_generation_mw
    FROM stg_fuel_mix
    GROUP BY date, settlement_period
),
joined AS (
    SELECT
        p.date,
        p.settlement_period,
        p.sbp_gbp_mwh,
        p.ssp_gbp_mwh,
        CASE
            WHEN f.total_generation_mw = 0 OR f.total_generation_mw IS NULL THEN NULL
            ELSE (f.wind_generation_mw * 100.0) / f.total_generation_mw
        END AS wind_pct,
        c.gas_p_per_therm,
        c.carbon_eur_per_tco2,
        COALESCE(c.eur_gbp, 0.86) AS eur_gbp
    FROM stg_system_prices p
    LEFT JOIN fuel_by_sp f
        ON p.date = f.date
       AND p.settlement_period = f.settlement_period
    LEFT JOIN dim_commodity_prices c
        ON p.date = c.date
)
SELECT
    date,
    settlement_period,
    sbp_gbp_mwh,
    ssp_gbp_mwh,
    wind_pct,
    ((gas_p_per_therm / 100.0) / 0.0293071) AS gas_gbp_mwh,
    (carbon_eur_per_tco2 * eur_gbp * 0.36) AS carbon_gbp_mwh,
    (
        sbp_gbp_mwh
        - (((gas_p_per_therm / 100.0) / 0.0293071) * 1.9)
    ) AS spark_spread_gbp_mwh,
    (
        sbp_gbp_mwh
        - (((gas_p_per_therm / 100.0) / 0.0293071) * 1.9)
        - (carbon_eur_per_tco2 * eur_gbp * 0.36)
    ) AS clean_spark_spread_gbp_mwh
FROM joined;

CREATE INDEX IF NOT EXISTS idx_fact_power_market_date_sp
    ON fact_power_market (date, settlement_period);
