markdown

\# 📊 Executive Data Assistant (Text-to-SQL Prototype)



A lightweight, governed natural-language analytics application that enables non-technical stakeholders to query business metrics in plain English—complete with automated SQL auditing and read-only guardrails.



\---



\## 🎯 Business Problem \& Architectural Approach



Growth-stage and mid-sized organizations often face a bottleneck between executive decision-making and data engineering: leaders need fast answers on revenue, retention, and churn, while lean data teams are bogged down by ad-hoc SQL requests. 



However, deploying unchecked generative AI on company data introduces two major risks: \*\*hallucinated metrics\*\* and \*\*data security vulnerabilities\*\*.



This prototype demonstrates a pragmatic, production-minded architecture designed to solve both challenges:

\* \*\*Speed to Value:\*\* Built with a lightweight, low-cost stack (\*\*Python, DuckDB, Streamlit, OpenAI API\*\*) to validate stakeholder adoption before investing in heavy infrastructure.

\* \*\*Executive Trust (Transparency Layer):\*\* Every answer exposes the underlying generated SQL query so analysts and executives can audit the exact logic behind the numbers.

\* \*\*Built-in Governance:\*\* Enforces strict read-only database connections (`read\_only=True`), deterministic prompting (`temperature=0`), and schema-bounded context to prevent destructive queries or schema hallucination.



\---



\## 🛠️ Tech Stack



\* \*\*Application Layer:\*\* \[Streamlit](https://streamlit.io) (rapid, interactive UI for stakeholder self-service)

\* \*\*Analytical Engine:\*\* \[DuckDB](https://duckdb.org) (in-process OLAP database; zero-cost local execution with seamless parity to cloud data warehouses)

\* \*\*AI Orchestration:\*\* OpenAI API (`gpt-4o-mini` for low-latency, cost-effective SQL generation)

\* \*\*Data Manipulation:\*\* Python \& Pandas



\---



\## 🚀 Quickstart Guide



\### 1. Clone the Repository \& Set Up Environment

```bash

git clone https://github.com

cd exec-data-chat



python -m venv venv

\# Windows:

venv\\Scripts\\activate

\# Mac/Linux:

source venv/bin/activate



pip install streamlit duckdb openai pandas

```



\### 2. Initialize the Sample Database

Generate the local DuckDB instance populated with sample SaaS subscription, MRR, and churn data:

```bash

python setup\_db.py

```



\### 3. Launch the Application

```bash

streamlit run app.py

```

Enter your OpenAI API key in the application sidebar and test plain-English queries such as:

\* \*"What is our total churned MRR by segment in Q3?"\*

\* \*"Which region has the highest active Enterprise revenue?"\*

\* \*"List the top reasons for customer churn across all quarters."\*



\---



\## 🏗️ Path to Production (Scaling Roadmap)



While this repository uses DuckDB for zero-cost local prototyping, the architecture is modular and designed for straightforward enterprise scaling:



1\. \*\*Cloud Warehouse Migration:\*\* Swap the local DuckDB connector for `snowflake-connector-python` or `databricks-sql-connector` using role-based access control (RBAC) service accounts.

2\. \*\*Semantic Layer Integration:\*\* Connect the prompt context directly to \*\*dbt (data build tool)\*\* manifest files (`manifest.json`) so the LLM leverages documented business definitions and certified metrics rather than raw table schemas.

3\. \*\*Automated Visualization \& Caching:\*\* Integrate Plotly for dynamic chart rendering and implement query caching to optimize API token spend (FinOps).

4\. \*\*Evaluation \& Observability:\*\* Add automated query logging and a golden-dataset test suite to monitor SQL accuracy over time.



\---



\## 📁 Repository Structure

```text

├── app.py                  # Main Streamlit UI, LLM prompt guardrails, and query execution

├── setup\_db.py             # Script to initialize and seed the local DuckDB database

├── business\_data.duckdb    # Local analytical database (generated upon setup)

└── README.md               # Architecture overview and documentation

```

