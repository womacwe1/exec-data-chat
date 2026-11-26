import duckdb
import pandas as pd

con = duckdb.connect('business_data.duckdb')

data = {
    'customer_id': ['C001', 'C002', 'C003', 'C004', 'C005', 'C006'],
    'segment': ['Enterprise', 'Mid-Market', 'SMB', 'Mid-Market', 'Enterprise', 'SMB'],
    'region': ['North America', 'Europe', 'North America', 'APAC', 'North America', 'Europe'],
    'mrr': list((12000, 4500, 1200, 3800, 15000, 950)),
    'status': ['Active', 'Churned', 'Active', 'Churned', 'Active', 'Churned'],
    'churn_reason': [None, 'Pricing increase', None, 'Missing feature', None, 'Budget cuts'],
    'quarter': ['Q3', 'Q3', 'Q3', 'Q3', 'Q4', 'Q4']
}

df = pd.DataFrame(data)
con.execute('CREATE OR REPLACE TABLE subscriptions AS SELECT * FROM df')
print('Database created successfully!')
con.close()
