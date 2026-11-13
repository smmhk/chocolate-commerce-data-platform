# Chocolate Commerce Data Platform · dbt

This dbt project transforms raw Online and Square data in BigQuery for reporting. Kestra loads the source data into the warehouse. dbt reads those raw datasets and builds analytics models in a separate development dataset.

## Current status

The first Online Orders staging view is built and verified in BigQuery at `chocolate-data-platform.dbt_dev.stg_online_orders`. It selects the order ID, channel, status, total amount, and creation timestamp from `raw_online.orders`. The model exposes `created_at` as `order_created_at`.

## Run locally

From the repository root, activate your Python virtual environment and install the BigQuery adapter. With Google Cloud CLI installed, sign in using an account that can access the project.

```powershell
python -m pip install dbt-bigquery
gcloud auth application-default login
cd chocolate_dbt
dbt debug
dbt run --select stg_online_orders
```

Use the profile name specified by `profile:` in `dbt_project.yml`. The local connection settings belong in `$HOME/.dbt/profiles.yml`, outside the repository.

| Profile setting | Value |
|---|---|
| Adapter | `bigquery` |
| Authentication method | `oauth` |
| Project | `chocolate-data-platform` |
| Development dataset | `dbt_dev` |
| Location | `us-east1` |

After the model runs, open `dbt_dev` in BigQuery Explorer or verify the view with this query.

```sql
select *
from `chocolate-data-platform.dbt_dev.stg_online_orders`
limit 10;
```

## Model layers

| Layer | Role | Status |
|---|---|---|
| Staging | Select and standardize fields from each raw source table | First Online Orders view verified |
| Intermediate | Join staging models and align Online and Square business rules | Planned |
| Marts | Publish datasets for reporting and dashboards | Planned |

The first model lives at `models/staging/stg_online_orders.sql`. Its source is declared in `models/staging/_online__sources.yml`. The next step is to profile the raw order status values, apply any confirmed cleaning rules in staging, and add order ID tests once the expected row grain is verified.
