from textwrap import dedent
from crewai import Agent, Task
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.tools.sql_database.tool import (
    InfoSQLDatabaseTool,
    ListSQLDatabaseTool,
    QuerySQLCheckerTool,
    QuerySQLDataBaseTool,
)
from crewai_tools import tool

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