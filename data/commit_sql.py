import sqlite3

conn = sqlite3.connect(r"C:\Users\callu\PycharmProjects\Energy Market Trader Job Project\gb-power-market\power_market.db")
cursor = conn.cursor()


cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables in DB:", cursor.fetchall())

cursor.executescript("""
-- Wind suppression
DROP VIEW IF EXISTS wind_suppression;
DROP TABLE IF EXISTS wind_suppression;

CREATE TABLE wind_suppression AS
SELECT
    f.settlementDate AS date,
    ROUND(SUM(CASE 
        WHEN f.fuelType = 'WIND' THEN f.generation 
        ELSE 0 END
    ) * 100.0 / NULLIF(SUM(f.generation), 0), 1) AS wind_pct,
    ROUND(AVG(s.systemBuyPrice), 2)     AS avg_price,
    ROUND(AVG(s.clean_spark_spread), 2) AS avg_css
FROM fuel_mix f
JOIN spreads s 
    ON DATE(f.settlementDate) = DATE(s.date)
GROUP BY f.settlementDate;

-- Price duration
DROP VIEW IF EXISTS price_duration;
DROP TABLE IF EXISTS price_duration;

CREATE TABLE price_duration AS
SELECT
    systemBuyPrice AS price,
    ROW_NUMBER() OVER (ORDER BY systemBuyPrice DESC) AS rank_desc
FROM spreads
WHERE systemBuyPrice IS NOT NULL;

-- Negative price events
DROP VIEW IF EXISTS negative_price_events;
DROP TABLE IF EXISTS negative_price_events;

CREATE TABLE negative_price_events AS
SELECT
    date,
    settlementPeriod,
    ROUND(systemBuyPrice, 2)     AS sbp,
    ROUND(clean_spark_spread, 2) AS css,
    ROUND(gas_p_therm, 2)        AS gas,
    ROUND(carbon_eur_mwh, 2)     AS carbon
FROM spreads
WHERE systemBuyPrice < 0
ORDER BY systemBuyPrice ASC;
""")

conn.commit()
conn.close()