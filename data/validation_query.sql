-- Range check for clean spark spread (GBP/MWh)
SELECT
    MIN(clean_spark_spread_gbp_mwh) AS min_css,
    MAX(clean_spark_spread_gbp_mwh) AS max_css,
    ROUND(AVG(clean_spark_spread_gbp_mwh), 2) AS avg_css
FROM fact_power_market;

-- Core null checks: no null key fields in Power BI fact table
SELECT
    SUM(CASE WHEN date IS NULL THEN 1 ELSE 0 END) AS null_date,
    SUM(CASE WHEN settlement_period IS NULL THEN 1 ELSE 0 END) AS null_settlement_period,
    SUM(CASE WHEN sbp_gbp_mwh IS NULL THEN 1 ELSE 0 END) AS null_sbp,
    SUM(CASE WHEN ssp_gbp_mwh IS NULL THEN 1 ELSE 0 END) AS null_ssp
FROM fact_power_market;

-- Daily shape check: should be 48 settlement periods per full day
SELECT
    date,
    COUNT(*) AS row_count
FROM fact_power_market
GROUP BY date
ORDER BY date;

-- Monthly market signal summary
SELECT
    SUBSTR(date, 1, 7) AS month,
    ROUND(AVG(sbp_gbp_mwh), 2) AS avg_sbp,
    ROUND(AVG(wind_pct), 2) AS avg_wind_pct,
    ROUND(AVG(clean_spark_spread_gbp_mwh), 2) AS avg_css
FROM fact_power_market
GROUP BY month
ORDER BY month;