import streamlit as st
import pandas as pd
import sqlite3
import os
from pathlib import Path
from textwrap import dedent
from typing import Dict, Any
from crewai import Agent, Crew, Task, Process
from langchain_community.utilities.sql_database import SQLDatabase
from database_utils import setup_database, get_table_info
from nlp_utils import setup_anthropic_client, nl_to_sql
from crewai_components import create_agents, create_tasks

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