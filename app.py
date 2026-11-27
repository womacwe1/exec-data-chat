import streamlit as st
import duckdb
import pandas as pd
from openai import OpenAI

st.set_page_config(page_title="Executive Data Assistant", layout="centered")
st.title("📊 Executive Data Assistant")
st.caption("Ask plain-English questions powered by a governed dbt Customer Health Mart.")

# Sidebar for API key & Governance context
api_key = st.sidebar.text_input("OpenAI API Key", type="password")
st.sidebar.divider()
st.sidebar.markdown("**Governance Layer**")
st.sidebar.info("Connected to `mart_customer_health` (verified via automated dbt schema & quality tests).")

# Define the governed dbt mart schema so the AI uses certified business definitions
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

question = st.text_input(
    "What would you like to know?",
    placeholder="e.g., Compare total ARR, critical tickets, and average CSAT by account status"
)

if st.button("Run Analysis") and question:
    if not api_key:
        st.error("Please enter your OpenAI API key in the sidebar.")
    else:
        client = OpenAI(api_key=api_key)
        
        # Step 1: Translate English to SQL against the governed mart
        prompt = f"""
        You are a senior data analyst. Convert the user's question into a valid DuckDB SQL query.
        Use ONLY the governed mart table provided below. Return ONLY the raw SQL query—no markdown, no explanations.
        Only generate SELECT statements.
        
        {SCHEMA_CONTEXT}
        
        Question: {question}
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        
        sql_query = response.choices[0].message.content.strip().replace("```sql", "").replace("```", "")
        
        # Step 2: Execute SQL safely against DuckDB
        try:
            con = duckdb.connect("business_data.duckdb", read_only=True)
            result_df = con.execute(sql_query).df()
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
                chart_df = result_df.set_index(cat_cols)[metric_cols]
                st.bar_chart(chart_df)
            
            # Step 5: Governance & Audit Trail
            with st.expander("View Generated SQL (Governance & Audit Trail)"):
                st.code(sql_query, language="sql")
                
        except Exception as e:
            st.error(f"Query execution failed: {e}")