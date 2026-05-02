CREATE VIEW IF NOT EXISTS price_duration AS
SELECT
    systemBuyPrice AS price,
    ROW_NUMBER() OVER (ORDER BY systemBuyPrice DESC) AS rank_desc
FROM spreads
WHERE systemBuyPrice IS NOT NULL;