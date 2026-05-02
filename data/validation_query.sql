-- Spot check: are spreads in a plausible range? (expect roughly -£20 to +£60)
SELECT MIN(clean_spark_spread), MAX(clean_spark_spread),
       ROUND(AVG(clean_spark_spread), 2) as avg_css
FROM spreads;

-- Check for NULLs — means the date join failed somewhere
SELECT COUNT(*) as null_count
FROM spreads
WHERE clean_spark_spread IS NULL;

-- Monthly average clean spark spread
SELECT substr(date, 1, 7) as month,
       ROUND(AVG(clean_spark_spread), 2) as avg_css,
       ROUND(AVG(spark_spread), 2) as avg_ss
FROM spreads
GROUP BY month
ORDER BY month;