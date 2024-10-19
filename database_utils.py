import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path

@st.cache_resource
def setup_database(csv_files, db_name="uk_biobank.db"):
    engine = sqlite3.connect(db_name)
    
    for file in csv_files:
        df = pd.read_csv(file, low_memory=False)
        table_name = Path(file).stem
        df.to_sql(table_name, engine, if_exists='replace', index=False)
    
    return db_name

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