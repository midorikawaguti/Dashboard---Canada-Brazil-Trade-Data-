# Canada - Brazil: Dashboard Trade Data

## Description

The project analyses Canadian export data sourced from Statistics Canada, covering the period 2024–2025, with the goal of building a Looker Studio dashboard for business decision-makers tracking bilateral trade flows.

## Dataset

The raw data consists of CSV files from Statistics Canada export records. Files covers export data for a specific Canadian province and period. Combined, the dataset spans approximately 2.5 million rows.

Each row represents one trade record:
- **Period** — Year-month of the export (e.g. 2024-03-01)
- **Commodity** — HS code and description (e.g. 8421.21.00 – Filtering or purifying machinery)
-	**Province** — Canadian province of export origin
-	**Country** — Destination/Origin country
-	**State** — US state (where applicable)
-	**Value ($)** — Total trade value in Canadian dollars
-	**Quantity** — Reported quantity
-	**Unit of measure** — The unit associated with the quantity

