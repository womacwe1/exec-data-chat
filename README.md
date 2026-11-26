# Executive Data Assistant

A governed natural-language analytics app built with Python, DuckDB, Streamlit, and OpenAI. Non-technical leaders can ask plain-English business questions and receive audited SQL queries, structured data tables, and automatic charts.

## Key Capabilities

* **Multi-Table Relational Joins:** Connects `subscriptions` (MRR, customer segments, churn reasons) with `support_tickets` (priority, resolution hours, CSAT scores) via `customer_id` for cross-functional insights.
* **Automated Visual Summaries:** Inspects query outputs and automatically renders bar charts when categorical labels are paired with numeric metrics, while filtering out ID fields.
* **Built-In Governance:** Uses read-only DuckDB connections (`read_only=True`), deterministic prompting (`temperature=0`), and an expandable SQL audit trail so leaders can verify every number.

## Data Model

* **`subscriptions`:** `customer_id`, `company_name`, `segment`, `region`, `mrr`, `status`, `churn_reason`, `quarter`
* **`support_tickets`:** `ticket_id`, `customer_id`, `category`, `priority`, `resolution_hours`, `csat_score`

## Quickstart

1. **Clone and set up the environment:**
   ```bash
   git clone https://github.com
   cd exec-data-chat
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Seed the local database:**
   ```bash
   python setup_db.py
   ```

3. **Run the app:**
   ```bash
   streamlit run app.py
   ```

## Example Prompts to Try

* *"Compare average ticket resolution hours and CSAT scores between Active and Churned customers."*
* *"Which churned companies had Critical support tickets, and what was their MRR?"*
* *"Show total MRR by customer segment."*

## Scaling Roadmap

* **Cloud Warehouse:** Replace DuckDB with Snowflake or Databricks using read-only RBAC service accounts.
* **Semantic Layer:** Feed dbt `manifest.json` definitions into the prompt context for standardized business metrics.
* **FinOps & Testing:** Add query caching to lower token usage and a golden-dataset test suite to track SQL accuracy.

