# Instructions for Implementing the Enhanced UK Biobank Query App

Follow these detailed steps to create an advanced UK Biobank Query App using Streamlit, CrewAI, and Anthropic's language models. This app allows users to query a large database using natural language, converts the query to SQL, executes it, and provides an analysis of the results.

## 1. Set Up the Environment

1.1. Install required libraries:
```
pip install streamlit pandas crewai langchain anthropic
```

1.2. Set up your Anthropic API key in Streamlit's secrets management:
- Create a file `.streamlit/secrets.toml` in your project directory
- Add the following line: `ANTHROPIC_API_KEY = "your_api_key_here"`

## 2. Import Required Libraries

Add the following imports at the top of your Python file:

```python
import streamlit as st
import pandas as pd
import sqlite3
import os
from pathlib import Path
from textwrap import dedent
from typing import Dict, Any
from crewai import Agent, Crew, Task, Process
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.tools.sql_database.tool import (
    InfoSQLDatabaseTool,
    ListSQLDatabaseTool,
    QuerySQLCheckerTool,
    QuerySQLDataBaseTool,
)
from langchain_core.prompts import ChatPromptTemplate
import anthropic
from crewai_tools import tool
```

## 3. Implement Database Setup Functions

3.1. Create a function to set up the database:

```python
@st.cache_resource
def setup_database(csv_files, db_name="uk_biobank.db"):
    engine = sqlite3.connect(db_name)
    
    for file in csv_files:
        df = pd.read_csv(file, low_memory=False)
        table_name = Path(file).stem
        df.to_sql(table_name, engine, if_exists='replace', index=False)
    
    return db_name
```

3.2. Create a function to get table information:

```python
@st.cache_data
def get_table_info(db_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    table_info = {}
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table[0]});")
        columns = cursor.fetchall()
        table_info[table[0]] = [col[1] for col in columns]
    
    conn.close()
    return table_info
```

## 4. Implement Anthropic Client Setup and Query Conversion

4.1. Set up the Anthropic client:

```python
def setup_anthropic_client():
    return anthropic.Anthropic()
```

4.2. Implement natural language to SQL conversion:

```python
def nl_to_sql(client, question, schema):
    message = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1000,
        temperature=0,
        system="You are an expert in converting natural language questions to SQL queries. Use the provided schema to create accurate SQL queries.",
        messages=[
            {
                "role": "user",
                "content": f"Convert the following question to a SQL query using this schema:\n{schema}\n\nQuestion: {question}"
            }
        ]
    )
    return message.content
```

## 5. Implement CrewAI Tools

Create the following tool functions:

```python
@tool("list_tables")
def list_tables(db: SQLDatabase) -> str:
    """List the available tables in the database"""
    return ListSQLDatabaseTool(db=db).invoke("")

@tool("tables_schema")
def tables_schema(db: SQLDatabase, tables: str) -> str:
    """
    Input is a comma-separated list of tables, output is the schema and sample rows
    for those tables. Be sure that the tables actually exist by calling `list_tables` first!
    """
    return InfoSQLDatabaseTool(db=db).invoke(tables)

@tool("execute_sql")
def execute_sql(db: SQLDatabase, sql_query: str) -> str:
    """Execute a SQL query against the database. Returns the result"""
    return QuerySQLDataBaseTool(db=db).invoke(sql_query)

@tool("check_sql")
def check_sql(db: SQLDatabase, sql_query: str) -> str:
    """
    Use this tool to double check if your query is correct before executing it.
    """
    return QuerySQLCheckerTool(db=db, llm=None).invoke({"query": sql_query})
```

## 6. Implement CrewAI Agents

Create a function to set up the agents:

```python
def create_agents(db: SQLDatabase):
    sql_dev = Agent(
        role="Senior Database Developer",
        goal="Construct and execute SQL queries based on a request",
        backstory=dedent(
            """
            You are an experienced database engineer who is master at creating efficient and complex SQL queries.
            You have a deep understanding of how different databases work and how to optimize queries.
            """
        ),
        tools=[
            lambda: list_tables(db),
            lambda tables: tables_schema(db, tables),
            lambda query: execute_sql(db, query),
            lambda query: check_sql(db, query)
        ],
        allow_delegation=False,
    )

    data_analyst = Agent(
        role="Senior Data Analyst",
        goal="You receive data from the database developer and analyze it",
        backstory=dedent(
            """
            You have deep experience with analyzing datasets using Python.
            Your work is always based on the provided data and is clear,
            easy-to-understand and to the point. You have attention
            to detail and always produce very detailed work (as long as you need).
            """
        ),
        allow_delegation=False,
    )

    report_writer = Agent(
        role="Senior Report Editor",
        goal="Write an executive summary type of report based on the work of the analyst",
        backstory=dedent(
            """
            Your writing style is well known for clear and effective communication.
            You always summarize long texts into bullet points that contain the most
            important details.
            """
        ),
        allow_delegation=False,
    )

    return sql_dev, data_analyst, report_writer
```

## 7. Implement CrewAI Tasks

Create a function to set up the tasks:

```python
def create_tasks(sql_dev, data_analyst, report_writer):
    extract_data = Task(
        description="Extract data that is required for the query {query}.",
        expected_output="Database result for the query",
        agent=sql_dev,
    )

    analyze_data = Task(
        description="Analyze the data from the database and write an analysis for {query}.",
        expected_output="Detailed analysis text",
        agent=data_analyst,
        context=[extract_data],
    )

    write_report = Task(
        description=dedent(
            """
            Write an executive summary of the report from the analysis. The report
            must be less than 100 words.
            """
        ),
        expected_output="Markdown report",
        agent=report_writer,
        context=[analyze_data],
    )

    return extract_data, analyze_data, write_report
```

## 8. Implement the Main Streamlit App

Create the main function for the Streamlit app:

```python
def main():
    st.set_page_config(page_title="UK Biobank Query App", layout="wide")
    st.title("UK Biobank Query App")

    # Database setup
    csv_files = st.text_input("Enter paths to your CSV files (comma-separated):").split(',')
    if csv_files and csv_files[0]:
        with st.spinner("Setting up database..."):
            db_name = setup_database(csv_files)
        st.success("Database setup complete!")
    else:
        st.warning("Please enter paths to your CSV files.")
        return

    # Get table info
    table_info = get_table_info(db_name)
    
    # Set up SQLDatabase
    db = SQLDatabase.from_uri(f"sqlite:///{db_name}")
    
    # Set up Anthropic client
    anthropic_client = setup_anthropic_client()
    
    # User input
    user_question = st.text_area("Enter your question about the UK Biobank data:")
    
    if user_question:
        try:
            with st.spinner("Processing your question..."):
                # Convert natural language to SQL
                sql_query = nl_to_sql(anthropic_client, user_question, str(table_info))
                
                st.subheader("Generated SQL Query:")
                st.code(sql_query, language="sql")
                
                # Set up CrewAI
                sql_dev, data_analyst, report_writer = create_agents(db)
                extract_data, analyze_data, write_report = create_tasks(sql_dev, data_analyst, report_writer)
                
                crew = Crew(
                    agents=[sql_dev, data_analyst, report_writer],
                    tasks=[extract_data, analyze_data, write_report],
                    process=Process.sequential,
                    verbose=2,
                )
                
                # Run CrewAI
                result = crew.kickoff(inputs={"query": user_question})
                
                # Display the result
                st.subheader("Analysis:")
                st.write(result)
            
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
    
    # Display database schema
    with st.sidebar.expander("Database Schema", expanded=True):
        for table, columns in table_info.items():
            st.sidebar.subheader(table)
            st.sidebar.write(", ".join(columns))

if __name__ == "__main__":
    main()
```

## 9. Run the App

Save all the code in a file named `app.py` and run it using the following command:

```
streamlit run app.py
```

## 10. Additional Considerations

- Ensure that the CSV files containing the UK Biobank data are accessible to the app.
- The app currently uses SQLite for simplicity, but for large datasets, consider using a more robust database system like PostgreSQL.
- Implement proper error handling and user feedback throughout the app.
- Consider adding data visualization features to enhance the analysis presentation.
- Implement user authentication if dealing with sensitive data.
- Optimize database queries and implement caching for frequently asked questions to improve performance.

By following these instructions, you will create a sophisticated UK Biobank Query App that allows users to interact with the database using natural language, provides SQL transparency, and offers detailed analysis of the queried data.