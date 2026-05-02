CREATE VIEW IF NOT EXISTS negative_price_events AS
SELECT
    date,
    settlementPeriod,
    ROUND(systemBuyPrice, 2)      AS sbp,
    ROUND(clean_spark_spread, 2)  AS css,
    ROUND(gas_p_therm, 2)         AS gas,
    ROUND(carbon_eur_mwh, 2)      AS carbon
FROM spreads
WHERE systemBuyPrice < 0
ORDER BY systemBuyPrice ASC;