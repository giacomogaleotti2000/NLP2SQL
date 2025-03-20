import streamlit as st
from db_utils import create_db_connection, run_query
from sql_utils import generate_sql_query
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from visualization_utils import generate_visualization_code
import time

def main():
    st.title("Making Databases Promptable")
    
    # Initialize session state variables if they don't exist
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'viz_code' not in st.session_state:
        st.session_state.viz_code = None
    if 'sql_query' not in st.session_state:
        st.session_state.sql_query = None
    if 'query_run_id' not in st.session_state:
        st.session_state.query_run_id = None
    
    # Text input for user question
    user_question = st.text_area("Ask a question to your database:")
    
    if st.button("Get SQL Query & Execute") or st.session_state.df is not None:
        # Only run the query if the button was just pressed or we don't have results yet
        if st.session_state.query_run_id is None:
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
                st.session_state.sql_query = generate_sql_query(user_question, schema_info)
            
            conn = create_db_connection()
            if conn:
                with st.spinner("Executing query..."):
                    rows, columns = run_query(st.session_state.sql_query, conn)
                    conn.close()
                
                if rows and columns:
                    # Convert rows to a list of dicts for easier display
                    data = [dict(zip(columns, row)) for row in rows]
                    st.session_state.df = pd.DataFrame(data)
                    
                    # Generate a unique ID for this query run
                    st.session_state.query_run_id = str(int(time.time()))
                    
                    # Generate visualization code
                    with st.spinner("Generating visualization..."):
                        st.session_state.viz_code = generate_visualization_code(
                            user_question, 
                            st.session_state.df.columns.tolist(), 
                            schema_info
                        )
        
        # Display SQL query (whether we just generated it or are showing it from before)
        if st.session_state.sql_query:
            st.write("**Proposed SQL Query:**")
            st.code(st.session_state.sql_query, language="sql")
        
        # Display results (if any)
        if st.session_state.df is not None:
                
                st.write("**Query Results:**")
                st.dataframe(st.session_state.df)
                
                # Visualization section
                st.write("**Data Visualization:**")
                
                # Create tabs for auto and manual visualization
                viz_tab1, viz_tab2 = st.tabs(["AI-Generated Visualization", "Manual Visualization"])
                
                with viz_tab1:
                    # Display the generated code (collapsible)
                    with st.expander("View Visualization Code"):
                        st.code(st.session_state.viz_code, language="python")
                    
                    # Execute the visualization code
                    try:
                        # Safe execution of the generated code
                        local_vars = {"df": st.session_state.df, "px": px, "go": go, "st": st}
                        exec(st.session_state.viz_code, globals(), local_vars)
                    except Exception as e:
                        st.error(f"Error in visualization: {str(e)}")
                        st.write("Displaying a default visualization instead:")
                        # Default visualization as fallback
                        if len(st.session_state.df) > 0:
                            numeric_cols = st.session_state.df.select_dtypes(include=['float64', 'int64']).columns.tolist()
                            if 'Date' in st.session_state.df.columns and len(numeric_cols) > 0:
                                st.line_chart(st.session_state.df.set_index('Date')[numeric_cols[:3]])
                            elif len(numeric_cols) > 0:
                                st.bar_chart(st.session_state.df[numeric_cols[:3]])
                
                with viz_tab2:
                    st.write("Create your own visualization:")
                    
                    # Extract column types
                    numeric_cols = st.session_state.df.select_dtypes(include=['float64', 'int64']).columns.tolist()
                    categorical_cols = st.session_state.df.select_dtypes(include=['object']).columns.tolist()
                    date_cols = [col for col in st.session_state.df.columns if 'date' in col.lower() or st.session_state.df[col].dtype == 'datetime64[ns]']
                    
                    # Chart type selection
                    chart_type = st.selectbox(
                        "Select chart type:",
                        ["Line Chart", "Bar Chart", "Scatter Plot", "Pie Chart", "Heatmap", "Box Plot"]
                    )
                    
                    if chart_type in ["Line Chart", "Bar Chart", "Scatter Plot"]:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            x_axis = st.selectbox("X-axis:", st.session_state.df.columns.tolist())
                        
                        with col2:
                            # Multi-select for y-axis in line and bar charts
                            if chart_type in ["Line Chart", "Bar Chart"]:
                                y_axis = st.multiselect("Y-axis:", numeric_cols, default=numeric_cols[:1] if numeric_cols else [])
                            else:
                                y_axis = st.selectbox("Y-axis:", numeric_cols if numeric_cols else st.session_state.df.columns.tolist())
                        
                        # Color by option for scatter
                        if chart_type == "Scatter Plot" and categorical_cols:
                            color_by = st.selectbox("Color by:", [None] + categorical_cols)
                        
                        # Create visualization based on selections
                        if chart_type == "Line Chart" and y_axis:
                            fig = px.line(st.session_state.df, x=x_axis, y=y_axis, title=f"{', '.join(y_axis)} over {x_axis}")
                            st.plotly_chart(fig, use_container_width=True)
                        
                        elif chart_type == "Bar Chart" and y_axis:
                            fig = px.bar(st.session_state.df, x=x_axis, y=y_axis, title=f"{', '.join(y_axis)} by {x_axis}")
                            st.plotly_chart(fig, use_container_width=True)
                        
                        elif chart_type == "Scatter Plot":
                            if 'color_by' in locals() and color_by:
                                fig = px.scatter(st.session_state.df, x=x_axis, y=y_axis, color=color_by, title=f"{y_axis} vs {x_axis} by {color_by}")
                            else:
                                fig = px.scatter(st.session_state.df, x=x_axis, y=y_axis, title=f"{y_axis} vs {x_axis}")
                            st.plotly_chart(fig, use_container_width=True)
                    
                    elif chart_type == "Pie Chart" and categorical_cols:
                        category = st.selectbox("Category:", categorical_cols)
                        values = st.selectbox("Values:", numeric_cols if numeric_cols else st.session_state.df.columns.tolist())
                        
                        fig = px.pie(st.session_state.df, names=category, values=values, title=f"{values} distribution by {category}")
                        st.plotly_chart(fig, use_container_width=True)
                    
                    elif chart_type == "Heatmap" and numeric_cols:
                        if len(numeric_cols) >= 2:
                            correlation = st.session_state.df[numeric_cols].corr()
                            fig = go.Figure(data=go.Heatmap(
                                z=correlation.values,
                                x=correlation.columns,
                                y=correlation.columns,
                                colorscale='Viridis'
                            ))
                            fig.update_layout(title="Correlation Heatmap")
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.warning("Not enough numeric columns for a correlation heatmap")
                    
                    elif chart_type == "Box Plot" and numeric_cols:
                        y_axis = st.selectbox("Value:", numeric_cols)
                        category = st.selectbox("Group by (optional):", [None] + categorical_cols)
                        
                        if category:
                            fig = px.box(st.session_state.df, x=category, y=y_axis, title=f"Distribution of {y_axis} by {category}")
                        else:
                            fig = px.box(st.session_state.df, y=y_axis, title=f"Distribution of {y_axis}")
                        st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("No results or query execution error.")
                
    # Add a clear button at the bottom to start over
    if st.session_state.df is not None:
        if st.button("New Query (Clear Results)"):
            # Reset all session state
            st.session_state.df = None
            st.session_state.viz_code = None
            st.session_state.sql_query = None 
            st.session_state.query_run_id = None
            # Force rerun to update UI
            st.experimental_rerun()

if __name__ == "__main__":
    main()