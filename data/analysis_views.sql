DROP VIEW IF EXISTS price_duration;
CREATE VIEW price_duration AS
SELECT
    sbp_gbp_mwh AS price,
    ROW_NUMBER() OVER (ORDER BY sbp_gbp_mwh DESC) AS rank_desc
FROM fact_power_market
WHERE sbp_gbp_mwh IS NOT NULL;

DROP VIEW IF EXISTS negative_price_events;
CREATE VIEW negative_price_events AS
SELECT
    date,
    settlement_period,
    ROUND(sbp_gbp_mwh, 2) AS sbp,
    ROUND(clean_spark_spread_gbp_mwh, 2) AS css,
    ROUND(gas_gbp_mwh, 2) AS gas,
    ROUND(carbon_gbp_mwh, 2) AS carbon
FROM fact_power_market
WHERE sbp_gbp_mwh < 0
ORDER BY sbp_gbp_mwh ASC;

DROP VIEW IF EXISTS carbon_quartiles;
CREATE VIEW carbon_quartiles AS
WITH ordered AS (
    SELECT
        carbon_gbp_mwh,
        ROW_NUMBER() OVER (ORDER BY carbon_gbp_mwh) AS rn,
        COUNT(*) OVER () AS n
    FROM fact_power_market
    WHERE carbon_gbp_mwh IS NOT NULL
)
SELECT
    (SELECT MIN(carbon_gbp_mwh) FROM ordered) AS min_value,
    (SELECT MAX(carbon_gbp_mwh) FROM ordered) AS max_value,
    (SELECT carbon_gbp_mwh FROM ordered WHERE rn = CAST(n * 0.25 AS INTEGER)) AS q1,
    (SELECT carbon_gbp_mwh FROM ordered WHERE rn = CAST(n * 0.50 AS INTEGER)) AS median,
    (SELECT carbon_gbp_mwh FROM ordered WHERE rn = CAST(n * 0.75 AS INTEGER)) AS q3;
