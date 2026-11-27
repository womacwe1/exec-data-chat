import streamlit as st
import duckdb
import pandas as pd
from pydantic import BaseModel, Field
from openai import OpenAI

st.set_page_config(page_title="Executive Data Assistant", layout="centered")
st.title("📊 Executive Data Assistant")
st.caption("Ask plain-English questions powered by a governed dbt Customer Health Mart & local Llama 3.2.")

# Sidebar showing Local LLM & Governance context
st.sidebar.markdown("**Model & FinOps Layer**")
st.sidebar.success("Running locally via Ollama (`llama3.2`) — $0 API cost & 100% private data.")
st.sidebar.divider()
st.sidebar.markdown("**Governance Layer**")
st.sidebar.info("Connected to `mart_customer_health` (verified via automated dbt schema & quality tests).")

# Define the governed dbt mart schema
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

# Pydantic schema to force clean SQL output without conversational text
class SQLResponse(BaseModel):
    sql_query: str = Field(
        description="Valid DuckDB SELECT query only. No markdown fences, no commentary, no explanations."
    )

def clean_sql(raw_text: str) -> str:
    text = raw_text.strip().replace("```sql", "").replace("```", "").strip()
    # Keep only up to the first semicolon so any trailing commentary is cut off
    if ";" in text:
        text = text.split(";")[0] + ";"
    return text.strip()

question = st.text_input(
    "What would you like to know?",
    placeholder="e.g., Compare total ARR, critical tickets, and average CSAT by account status"
)

if st.button("Run Analysis") and question:
    client = OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama"
    )
    
    # Step 1: Translate English to SQL against the governed mart using Pydantic
    prompt = f"""
    You are a senior data analyst. Convert the user's question into a valid DuckDB SQL query.
    Use ONLY the governed mart table provided below. Only generate SELECT statements.
    
    Strict DuckDB Rules:
    - Never reuse an existing column name (such as account_status) as an alias in the SELECT clause.
    - Never reference a SELECT column alias inside the same SELECT clause; use a CTE (WITH ...) if needed.
    
    {SCHEMA_CONTEXT}
    
    Question: {question}
    """
    
    with st.spinner("Generating governed SQL with Llama 3.2..."):
        response = client.beta.chat.completions.parse(
            model="llama3.2",
            messages=[{"role": "user", "content": prompt}],
            response_format=SQLResponse,
            temperature=0
        )
        sql_query = clean_sql(response.choices[0].message.parsed.sql_query)
    
    # Step 2: Execute SQL safely against DuckDB (with 1 automatic retry if DuckDB rejects the SQL)
    try:
        con = duckdb.connect("business_data.duckdb", read_only=True)
        try:
            result_df = con.execute(sql_query).df()
        except Exception as first_error:
            fix_prompt = f"""
            The following DuckDB SQL query failed with an error. Fix the query and return a valid DuckDB SELECT statement.
            Do not reuse existing column names as SELECT aliases.

            {SCHEMA_CONTEXT}

            Failed SQL:
            {sql_query}

            DuckDB Error:
            {first_error}
            """
            retry_response = client.beta.chat.completions.parse(
                model="llama3.2",
                messages=[{"role": "user", "content": fix_prompt}],
                response_format=SQLResponse,
                temperature=0
            )
            sql_query = clean_sql(retry_response.choices[0].message.parsed.sql_query)
            result_df = con.execute(sql_query).df()
        finally:
            con.close()
        
        # Step 3: Display Data Table
        st.subheader("Results")
        st.dataframe(result_df, use_container_width=True)
        
        # Step 4: Automated Visualization Layer
        cat_cols = result_df.select_dtypes(include=["object", "string", "category"]).columns.tolist()
        num_cols = result_df.select_dtypes(include=["number"]).columns.tolist()
        metric_cols = [c for c in num_cols if not c.lower().endswith("_id")]
        
        if len(result_df) > 1 and len(cat_cols) >= 1 and len(metric_cols) >= 1:
            st.subheader("Visual Summary")
            chart_df = result_df[[cat_cols[0]] + metric_cols].copy()
            st.bar_chart(chart_df, x=cat_cols[0], y=metric_cols)
        
        # Step 5: Governance & Audit Trail
        with st.expander("View Generated SQL (Governance & Audit Trail)"):
            st.code(sql_query, language="sql")
            
    except Exception as e:
        st.error(f"Query execution failed: {e}")
        st.code(sql_query, language="sql")