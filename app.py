import streamlit as st
import duckdb
import os
from openai import OpenAI

st.set_page_config(page_title="Executive Data Assistant", layout="centered")
st.title("📊 Executive Data Assistant")
st.caption("Ask plain-English questions about revenue, segments, and churn.")

# Sidebar for API key input (keeps credentials out of your code)
api_key = st.sidebar.text_input("OpenAI API Key", type="password")

# Define the schema context so the AI knows your exact table structure
SCHEMA_CONTEXT = """
Table name: subscriptions
Columns:
- customer_id (INTEGER)
- segment (VARCHAR: 'Enterprise', 'Mid-Market', 'SMB')
- region (VARCHAR: 'North America', 'Europe', 'APAC')
- mrr (INTEGER: Monthly Recurring Revenue in USD)
- status (VARCHAR: 'Active', 'Churned')
- churn_reason (VARCHAR: reason for churn, NULL if Active)
- quarter (VARCHAR: 'Q3', 'Q4')
"""

question = st.text_input("What would you like to know?", placeholder="e.g., What is our total churned MRR by segment in Q3?")

if st.button("Run Analysis") and question:
    if not api_key:
        st.error("Please enter your API key in the sidebar.")
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

        sql_query = response.choices[0].message.content.strip().replace("```sql", "").replace("```", "")

        # Step 2: Execute SQL safely against DuckDB
        try:
            con = duckdb.connect("business_data.duckdb", read_only=True)
            result_df = con.execute(sql_query).df()
            con.close()

            # Step 3: Display Results & Transparency Layer
            st.subheader("Results")
            st.dataframe(result_df, use_container_width=True)

            with st.expander("View Generated SQL (Governance & Audit Trail)"):
                st.code(sql_query, language="sql")

        except Exception as e:
            st.error(f"Query execution failed: {e}")