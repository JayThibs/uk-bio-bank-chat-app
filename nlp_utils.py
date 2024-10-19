import anthropic
import streamlit as st

def setup_anthropic_client():
    api_key = st.secrets["ANTHROPIC_API_KEY"]
    return anthropic.Anthropic(api_key=api_key)

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