import duckdb
import pandas as pd

# Connect to (or create) the local DuckDB database file
con = duckdb.connect("business_data.duckdb")

# Table 1: SaaS subscriptions, MRR, and churn data
subscriptions_data = {
    "customer_id": list(range(101, 107)),
    "company_name": ["Acme Corp", "Globex Systems", "BrightPath Retail", "Vertex Logistics", "Apex Health", "Summit Media"],
    "segment": ["Enterprise", "Mid-Market", "SMB", "Mid-Market", "Enterprise", "SMB"],
    "region": ["North America", "Europe", "North America", "APAC", "North America", "Europe"],
    "mrr": list((15000, 6500, 1200, 5800, 18500, 950)),
    "status": ["Active", "Churned", "Active", "Churned", "Active", "Churned"],
    "churn_reason": [None, "Pricing increase", None, "Missing feature", None, "Budget cuts"],
    "quarter": ["Q3", "Q3", "Q3", "Q3", "Q4", "Q4"]
}

# Table 2: Customer support interactions (linked via customer_id)
tickets_data = {
    "ticket_id": list(range(5001, 5009)),
    "customer_id": list((101, 102, 102, 104, 104, 106, 105, 102)),
    "category": ["Onboarding", "Billing", "API Bug", "Feature Request", "Downtime", "Integration", "Security Review", "Billing"],
    "priority": ["Low", "High", "Critical", "Medium", "Critical", "High", "Medium", "High"],
    "resolution_hours": [4.5, 48.0, 72.0, 36.0, 96.0, 60.0, 12.0, 52.0],
    "csat_score": list((5, 2, 1, 3, 1, 2, 5, 2))
}

df_subs = pd.DataFrame(subscriptions_data)
df_tickets = pd.DataFrame(tickets_data)

con.execute("CREATE OR REPLACE TABLE subscriptions AS SELECT * FROM df_subs")
con.execute("CREATE OR REPLACE TABLE support_tickets AS SELECT * FROM df_tickets")

print("Database created successfully with 'subscriptions' and 'support_tickets' tables!")
con.close()
