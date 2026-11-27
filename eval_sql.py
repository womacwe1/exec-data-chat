import time
import duckdb
import pandas as pd
from pydantic import BaseModel
from openai import OpenAI

# 1. Enforce structured SQL output (prevents conversational chatter from breaking execution)
class SQLResponse(BaseModel):
    sql_query: str

SCHEMA_CONTEXT = """
Table: mart_customer_health
Columns:
- customer_id (INTEGER)
- company_name (VARCHAR)
- segment (VARCHAR: 'Enterprise', 'Mid-Market', 'SMB')
- region (VARCHAR: 'North America', 'Europe', 'APAC')
- mrr (INTEGER)
- arr (INTEGER)
- account_status (VARCHAR: 'Active', 'Churned')
- churn_reason (VARCHAR)
- total_tickets (INTEGER)
- critical_tickets (INTEGER)
- avg_resolution_hours (FLOAT)
- avg_csat_score (FLOAT)
"""

# 2. Golden Dataset: Verified executive questions + ground-truth SQL
GOLDEN_DATASET = [
    {
        "id": "EVAL-01",
        "question": "What is the total ARR across all Active accounts?",
        "expected_sql": "SELECT SUM(arr) FROM mart_customer_health WHERE account_status = 'Active';"
    },
    {
        "id": "EVAL-02",
        "question": "How many total critical tickets were submitted by Churned accounts?",
        "expected_sql": "SELECT SUM(critical_tickets) FROM mart_customer_health WHERE account_status = 'Churned';"
    },
    {
        "id": "EVAL-03",
        "question": "Which company has the highest ARR?",
        "expected_sql": "SELECT company_name FROM mart_customer_health ORDER BY arr DESC LIMIT 1;"
    },
    {
        "id": "EVAL-04",
        "question": "What is the average CSAT score for Enterprise customers?",
        "expected_sql": "SELECT AVG(avg_csat_score) FROM mart_customer_health WHERE segment = 'Enterprise';"
    },
    {
        "id": "EVAL-05",
        "question": "Total churned MRR in Europe?",
        "expected_sql": "SELECT SUM(mrr) FROM mart_customer_health WHERE account_status = 'Churned' AND region = 'Europe';"
    }
]

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
con = duckdb.connect("business_data.duckdb", read_only=True)

results = []

print("Running Golden Dataset Evaluation against local Llama 3.2...\n")

for test in GOLDEN_DATASET:
    start_time = time.time()
    
    # Generate SQL with Pydantic schema enforcement
    response = client.beta.chat.completions.parse(
        model="llama3.2",
        messages=[
            {"role": "system", "content": f"Convert the question into a single DuckDB SELECT query using ONLY this schema:\n{SCHEMA_CONTEXT}"},
            {"role": "user", "content": test["question"]}
        ],
        response_format=SQLResponse,
        temperature=0
    )
    
    latency = round(time.time() - start_time, 2)
    generated_sql = response.choices[0].message.parsed.sql_query.strip()
    
    # Compare actual query result vs. expected ground truth result
    try:
        expected_val = con.execute(test["expected_sql"]).fetchone()
        actual_val = con.execute(generated_sql).fetchone()
        
        # Handle float rounding comparisons cleanly
        if isinstance(expected_val, float) and isinstance(actual_val, float):
            passed = round(expected_val, 2) == round(actual_val, 2)
        else:
            passed = expected_val == actual_val
            
        status = "PASS" if passed else f"FAIL (Expected {expected_val}, Got {actual_val})"
    except Exception as e:
        passed = False
        status = f"SQL ERROR: {e}"
        
    results.append({"id": test["id"], "passed": passed, "latency_sec": latency})
    print(f"[{test['id']}] {status} | Latency: {latency}s")
    print(f"   Q: {test['question']}")
    print(f"   Generated SQL: {generated_sql}\n")

con.close()

# 3. Print Executive Governance & FinOps Scorecard
eval_df = pd.DataFrame(results)
accuracy = round(eval_df["passed"].mean() * 100, 1)
avg_latency = round(eval_df["latency_sec"].mean(), 2)

print("=" * 55)
print(f"GOVERNANCE SCORECARD | Accuracy: {accuracy}% | Avg Latency: {avg_latency}s | Cost: $0.00")
print("=" * 55)
