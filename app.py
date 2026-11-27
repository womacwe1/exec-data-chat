import time
import streamlit as st
import duckdb
import pandas as pd
from pydantic import BaseModel
from openai import OpenAI

st.set_page_config(page_title="Executive Data Assistant", layout="centered")
st.title("📊 Executive Data Assistant")
st.caption("Ask plain-English questions powered by a governed dbt Customer Health Mart & local Llama 3.2.")

# Sidebar: Governance & FinOps Telemetry
st.sidebar.markdown("**Model & FinOps Layer**")
st.sidebar.success("Running locally via Ollama (`llama3.2`) — $0 API cost & 100% private data.")
st.sidebar.caption("Query caching enabled (`TTL = 1 hr`) to eliminate redundant LLM inference.")
st.sidebar.divider()
st.sidebar.markdown("**Governance Layer**")
st.sidebar.info("Connected to `mart_customer_health` with Pydantic SQL enforcement & read-only DuckDB lock.")

# 1. Pydantic Data Contract (Prevents conversational chatter from breaking SQL execution)
class SQLResponse(BaseModel):
    sql_query: str

SCHEMA_CONTEXT = """
Table: mart_customer_health
Description: Governed executive mart combining SaaS subscription revenue with aggregated customer support metrics.
Columns:
- customer_id (INTEGER, Primary Key)
- company_name (VARCHAR)
- segment (VARCHAR: 'Enterprise', 'Mid-Market', 'SMB')
- region (VARCHAR: 'North America', 'Europe', 'APAC')
- mrr (INTEGER: Monthly Recurring Revenue in USD)
- arr (INTEGER: Annual Recurring Revenue in USD, calculated as MRR * 12)
- account_status (VARCHAR: 'Active', 'Churned')
- churn_reason (VARCHAR: reason for churn, 'None' if Active)
- total_tickets (INTEGER: total support tickets submitted by the customer)
- critical_tickets (INTEGER: count of Critical priority support tickets)
- avg_resolution_hours (FLOAT: average hours to resolve support tickets)
- avg_csat_score (FLOAT: average Customer Satisfaction score from 1.0 to 5.0)
"""

# 2. Cached Inference & Query Execution (FinOps & Latency Optimization)
@st.cache_data(ttl=3600, show_spinner=True)
def run_governed_query(user_question: str):
    client = OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama"
    )
    
    prompt = f"""
    You are a senior data analyst. Convert the user's question into a single valid DuckDB SELECT query.
    Use ONLY the governed mart table provided below.
    Only generate SELECT statements.
    
    {SCHEMA_CONTEXT}
    """
    
    response = client.beta.chat.completions.parse(
        model="llama3.2",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_question}
        ],
        response_format=SQLResponse,
        temperature=0
    )
    
    sql_query = response.choices[0].message.parsed.sql_query.strip()
    
    # Defense-in-depth guardrail: block non-SELECT statements before hitting the database
    if not sql_query.upper().lstrip().startswith("SELECT"):
        raise ValueError("Governance Guardrail Triggered: Only read-only SELECT queries are permitted.")
    
    con = duckdb.connect("business_data.duckdb", read_only=True)
    result_df = con.execute(sql_query).df()
    con.close()
    
    return sql_query, result_df

question = st.text_input(
    "What would you like to know?",
    placeholder="e.g., Compare total ARR, critical tickets, and average CSAT by account status"
)

if st.button("Run Analysis") and question:
    start_time = time.time()
    try:
        with st.spinner("Running governed analysis..."):
            sql_query, result_df = run_governed_query(question.strip())
        
        elapsed = round(time.time() - start_time, 3)
        
        # Display Data Table & Latency Telemetry
        st.subheader("Results")
        st.caption(f"Completed in {elapsed}s (cached queries return in < 0.01s)")
        st.dataframe(result_df, use_container_width=True)
        
        # Automated Visualization Layer
        cat_cols = result_df.select_dtypes(include=["object", "string", "category"]).columns.tolist()
        num_cols = result_df.select_dtypes(include=["number"]).columns.tolist()
        metric_cols = [c for c in num_cols if not c.lower().endswith("_id")]
        
        if len(result_df) > 1 and len(cat_cols) >= 1 and len(metric_cols) >= 1:
            st.subheader("Visual Summary")
            chart_df = result_df[[cat_cols[0]] + metric_cols].copy()
            st.bar_chart(chart_df, x=cat_cols[0], y=metric_cols)
        
        # Governance & Audit Trail
        with st.expander("View Generated SQL (Governance & Audit Trail)"):
            st.code(sql_query, language="sql")
            
    except Exception as e:
        st.error(f"Execution blocked or failed: {e}")