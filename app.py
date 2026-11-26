import streamlit as st
import duckdb
import pandas as pd
from openai import OpenAI

st.set_page_config(page_title="Executive Data Assistant", layout="centered")
st.title("📊 Executive Data Assistant")
st.caption("Ask plain-English questions about revenue, churn, and customer support.")

# Sidebar for API key input
api_key = st.sidebar.text_input("OpenAI API Key", type="password")

# Define the two-table schema context so the AI knows how to join them
SCHEMA_CONTEXT = """
Table 1: subscriptions
Columns:
- customer_id (INTEGER, Primary Key)
- company_name (VARCHAR)
- segment (VARCHAR: 'Enterprise', 'Mid-Market', 'SMB')
- region (VARCHAR: 'North America', 'Europe', 'APAC')
- mrr (INTEGER: Monthly Recurring Revenue in USD)
- status (VARCHAR: 'Active', 'Churned')
- churn_reason (VARCHAR: reason for churn, NULL if Active)
- quarter (VARCHAR: 'Q3', 'Q4')

Table 2: support_tickets
Columns:
- ticket_id (INTEGER, Primary Key)
- customer_id (INTEGER, Foreign Key referencing subscriptions.customer_id)
- category (VARCHAR: 'Onboarding', 'Billing', 'API Bug', 'Feature Request', 'Downtime', 'Integration', 'Security Review')
- priority (VARCHAR: 'Low', 'Medium', 'High', 'Critical')
- resolution_hours (FLOAT: time in hours to resolve the ticket)
- csat_score (INTEGER: Customer Satisfaction score from 1 to 5)
"""

question = st.text_input(
    "What would you like to know?",
    placeholder="e.g., Compare average ticket resolution hours and CSAT scores by customer status"
)

if st.button("Run Analysis") and question:
    if not api_key:
        st.error("Please enter your OpenAI API key in the sidebar.")
    else:
        client = OpenAI(api_key=api_key)
        
        # Step 1: Translate English to SQL with strict guardrails
        prompt = f"""
        You are a senior data analyst. Convert the user's question into a valid DuckDB SQL query.
        Use ONLY the schema provided below. Return ONLY the raw SQL query—no markdown, no explanations.
        Only generate SELECT statements.
        
        {SCHEMA_CONTEXT}
        
        Question: {question}
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        
        # Note: use choices[0] to grab the first completion message
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
            # Detect text/category columns and numeric columns to auto-render a chart
            cat_cols = result_df.select_dtypes(include=["object", "string", "category"]).columns.tolist()
            num_cols = result_df.select_dtypes(include=["number"]).columns.tolist()
            
            # Exclude ID columns from being plotted as business metrics
            metric_cols = [c for c in num_cols if not c.lower().endswith("_id")]
            
            if len(result_df) > 1 and len(cat_cols) >= 1 and len(metric_cols) >= 1:
                st.subheader("Visual Summary")
                chart_df = result_df.set_index(cat_cols[0])[metric_cols]
                st.bar_chart(chart_df)
            
            # Step 5: Governance & Audit Trail
            with st.expander("View Generated SQL (Governance & Audit Trail)"):
                st.code(sql_query, language="sql")
                
        except Exception as e:
            st.error(f"Query execution failed: {e}")