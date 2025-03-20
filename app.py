from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
import streamlit as st
import openai
import pyodbc
import os

endpoint = "https://aihubtsprova4768698776.cognitiveservices.azure.com/openai/deployments/gpt-4o-mini"
model_name = "gpt-4o-mini"

client = ChatCompletionsClient(
    endpoint=endpoint,
    credential=AzureKeyCredential("DSEwkqJqsCAifHe5EAsRwXgvftKu0Sw4Fh3SGeVNlcGjinSTbuk0JQQJ99BCAC5RqLJXJ3w3AAAAACOG7dus"),
)

# For local dev, you might just store them in environment variables or directly in the code
# (not recommended for production):
server = "your-sql-server.database.windows.net"
database = "nl2sql_db"
username = "giacomogaleotti"
password = "Pollo008!"

# Set up the connection string for Azure SQL
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

def generate_sql_query(user_question, schema_info=None):
    """
    Use OpenAI ChatCompletion to transform the user question into a valid SQL query.
    
    Optionally, provide 'schema_info' (a string describing the DB schema) to help the model.
    """
    system_prompt = f"""
    You are a helpful assistant that transforms user questions into **valid** SQL queries.
    Here is the database schema:
    {schema_info or "No schema info provided."}

    Rules:
    1. Output **only** a valid SQL query (no code fences, no explanations).
    2. Do not include triple backticks or any additional formatting.
    3. Do not include any text outside the SQL query.
    """

    response = client.complete(
    messages=[
        SystemMessage(content=system_prompt),
        UserMessage(content=user_question)
    ],
    max_tokens=4096,
    temperature=1.0,
    top_p=1.0,
    model=model_name
    )
    
    sql_query = response.choices[0].message.content.strip()
    return sql_query

def run_query(query, conn):
    """
    Run the SQL query on the provided connection and return the rows.
    """
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

def main():
    st.title("Making Databases Promptable")
    
    # Text input for user question
    user_question = st.text_area("Ask a question about your database:")
    
    # Button to run the pipeline
    if st.button("Get SQL Query & Execute"):
        with st.spinner("Generating SQL query..."): 
            # Optionally pass known schema info
            schema_info ="""
                        The database has a single table "generation_data" with columns:

                        - index_id (INT)                -- Primary key / unique identifier
                        - Date (DATE)                   -- Date of generation data
                        - Region (VARCHAR(50))          -- Region name
                        - Thermal_Actual (DECIMAL(18,2))   -- Actual thermal generation
                        - Thermal_Estimated (DECIMAL(18,2)) -- Estimated thermal generation
                        - Nuclear_Actual (DECIMAL(18,2))    -- Actual nuclear generation
                        - Nuclear_Estimated (DECIMAL(18,2)) -- Estimated nuclear generation
                        - Hydro_Actual (DECIMAL(18,2))      -- Actual hydro generation
                        - Hydro_Estimated (DECIMAL(18,2))   -- Estimated hydro generation
                        """

            sql_query = generate_sql_query(user_question, schema_info)
        
        st.write("**Proposed SQL Query:**")
        st.code(sql_query, language="sql")
        
        conn = create_db_connection()
        if conn:
            with st.spinner("Executing query..."):
                rows, columns = run_query(sql_query, conn)
                conn.close()
                
            if rows and columns:
                # Convert rows to a list of dicts for easier display
                data = [dict(zip(columns, row)) for row in rows]
                st.write("**Query Results:**")
                st.dataframe(data)
            else:
                st.write("No results or query execution error.")

if __name__ == "__main__":
    main()
