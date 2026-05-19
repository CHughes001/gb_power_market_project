GB Power Market Pipeline

A small end-to-end data project exploring balancing prices, renewable penetration, and thermal generation economics in the GB power market.

The pipeline pulls data from Elexon BMRS and commodity price inputs, transforms it into a clean settlement-period dataset, and serves a single fact table for analysis in Power BI.

The project focuses on how intraday price shape, wind penetration, and clean spark spreads interact across different market conditions.

For the interactive dashboards and analysis, see the Projects section of my portfolio website:

callumhughesportfolio.netlify.app


Architecture Overview

The pipeline follows a simple three-layer structure:

Staging → raw-normalised BMRS and commodity data
Transformation → spread calculations and market metrics
Serving → Power BI-ready fact table

Core scripts:

scripts/fetch_data.py
scripts/load_commodity_prices.py
scripts/build_powerbi_fact.py
scripts/calculate_spreads.py

Main output table:

fact_power_market

Data Flow
flowchart LR
    A[Elexon BMRS API] --> B[stg_system_prices]
    A --> C[stg_fuel_mix]
    A --> D[stg_demand_indo]
    E[Gas + Carbon CSVs] --> F[dim_commodity_prices]
    B --> G[Transformation Layer]
    C --> G
    F --> G
    G --> H[fact_power_market]
    H --> I[Power BI Model]

Key Metrics

The dataset is built at settlement-period level (date + settlement_period) to preserve intraday market behaviour.

Main fields include:

sbp_gbp_mwh
ssp_gbp_mwh
wind_pct
gas_gbp_mwh
carbon_gbp_mwh
spark_spread_gbp_mwh
clean_spark_spread_gbp_mwh

Core calculations:

Spark spread = SBP - (gas_gbp_mwh * heat_rate)
Clean spark spread = spark_spread - carbon_gbp_mwh
Run the Pipeline

Install dependencies:

pip install pandas requests

Run the loaders:

python scripts/fetch_data.py
python scripts/load_commodity_prices.py
python scripts/build_powerbi_fact.py

Optional SQL materialisation:

sqlite3 power_market.db ".read data/build_powerbi_fact.sql"
Power BI

Connect Power BI to power_market.db and import fact_power_market.