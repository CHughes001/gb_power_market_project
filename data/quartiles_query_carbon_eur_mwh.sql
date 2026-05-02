WITH o AS (
    SELECT
        carbon_eur_mwh,
        ROW_NUMBER() OVER (ORDER BY carbon_eur_mwh) AS rn,
        COUNT(*) OVER () AS n
    FROM spreads
)
SELECT
    (SELECT MIN(carbon_eur_mwh) FROM o) AS min_value,
    (SELECT MAX(carbon_eur_mwh) FROM o) AS max_value,
    (SELECT carbon_eur_mwh FROM o WHERE rn = CAST(n*0.25 AS INT)) AS q1,
    (SELECT carbon_eur_mwh FROM o WHERE rn = CAST(n*0.50 AS INT)) AS median,
    (SELECT carbon_eur_mwh FROM o WHERE rn = CAST(n*0.75 AS INT)) AS q3;
