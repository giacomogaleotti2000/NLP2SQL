import streamlit as st
import pyodbc
import os

SQL_PASSWORD = os.getenv("SQL_PASSWORD")
server = "your-sql-server.database.windows.net"
database = "nl2sql_db"
username = "giacomogaleotti"
password = SQL_PASSWORD

connection_string = (
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER={server};DATABASE={database};"
    f"UID={username};PWD={password}"
)

def create_db_connection():
    """Create and return a connection to the Azure SQL database."""
    try:
        conn = pyodbc.connect(connection_string)
        return conn
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return None

def run_query(query, conn):
    """Run the SQL query on the provided connection and return the rows and columns."""
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        # Get column names
        columns = [desc[0] for desc in cursor.description]
        return rows, columns
    except Exception as e:
        st.error(f"Error running query: {e}")
        return None, None
