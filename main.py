import streamlit as st
from db_utils import create_db_connection, run_query
from sql_utils import generate_sql_query

def main():
    st.title("Making Databases Promptable")
    
    # Text input for user question
    user_question = st.text_area("Ask a question to your database:")
    
    if st.button("Get SQL Query & Execute"):
        with st.spinner("Generating SQL query..."):
            # Provide your database schema info
            schema_info = """
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
