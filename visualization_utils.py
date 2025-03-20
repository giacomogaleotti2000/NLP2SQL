import openai
import os
import json

def generate_visualization_code(user_question, columns, schema_info):
    """
    Generate visualization code based on user question and data columns.
    
    Args:
        user_question (str): The user's natural language question
        columns (list): List of column names available in the data
        schema_info (str): Database schema information
        
    Returns:
        str: Python code for visualization using Plotly and Streamlit
    """
    # Make sure your API key is set in environment variables
    client = openai.OpenAI(api_key=os.getenv("AZURE_KEY"))
    
    prompt = f"""
    Given a user question and the data columns from a SQL query result, generate Python code
    for data visualization using Plotly and Streamlit. The code should be executable directly.
    
    USER QUESTION: {user_question}
    
    AVAILABLE COLUMNS: {columns}
    
    DATABASE SCHEMA INFORMATION:
    {schema_info}
    
    Use pandas DataFrame named 'st.session_state.df' which already contains the query results.
    The visualization should focus on the most relevant aspects of the data based on the question.
    Generate only the visualization code using Plotly's px or go modules and Streamlit's st.plotly_chart().
    No imports needed as they are already available.
    The code should handle empty dataframes and include error handling.
    
    INSTRUCTIONS:
    1. Choose appropriate chart types (line, bar, scatter, pie, etc.) based on the data and question
    2. For time series data, prefer line charts with Date on x-axis
    3. For comparisons between categories, use bar or grouped bar charts
    4. For part-to-whole relationships, use pie charts or stacked bars
    5. Add proper titles, labels, and legends
    6. Use 'st.session_state.df' as the dataframe name, NOT just 'df'
    7. Add fig.update_layout(uirevision='constant') to prevent reloading on interaction
    8. Display summary statistics alongside visualizations when appropriate
    
    RETURN ONLY EXECUTABLE PYTHON CODE, NO EXPLANATIONS.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # or another appropriate model
            messages=[
                {"role": "system", "content": "You are a data visualization expert who generates Python code using Plotly and Streamlit."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1000
        )
        
        # Extract the code from the response
        visualization_code = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if visualization_code.startswith("```python"):
            visualization_code = visualization_code.replace("```python", "", 1)
        elif visualization_code.startswith("```"):
            visualization_code = visualization_code.replace("```", "", 1)
        if visualization_code.endswith("```"):
            visualization_code = visualization_code[:-3]
        
        # Add code to handle figure configuration to prevent interruptions
        additional_code = """
# Configure the figure to avoid full page refreshes on hover/click
if 'fig' in locals():
    fig.update_layout(
        uirevision='constant',
        hovermode='closest',
        clickmode='event',
    )
"""
        visualization_code = visualization_code.strip() + additional_code
        
        return visualization_code
        
    except Exception as e:
        # Fallback basic visualization code
        return """
# Basic fallback visualization
try:
    # Check if we have data
    if len(st.session_state.df) > 0:
        # Get numeric columns
        numeric_cols = st.session_state.df.select_dtypes(include=['float64', 'int64']).columns.tolist()
        
        if 'Date' in st.session_state.df.columns and len(numeric_cols) > 0:
            # Time series plot
            fig = px.line(st.session_state.df, x='Date', y=numeric_cols[:3], 
                     title='Time Series of Selected Metrics')
            fig.update_layout(uirevision='constant')  # Prevent refresh on interaction
            st.plotly_chart(fig, use_container_width=True)
        elif 'Region' in st.session_state.df.columns and len(numeric_cols) > 0:
            # Bar chart by region
            fig = px.bar(st.session_state.df, x='Region', y=numeric_cols[0], 
                    title=f'Comparison of {numeric_cols[0]} by Region')
            fig.update_layout(uirevision='constant')  # Prevent refresh on interaction
            st.plotly_chart(fig, use_container_width=True)
        elif len(numeric_cols) >= 2:
            # Scatter plot of first two numeric columns
            fig = px.scatter(st.session_state.df, x=numeric_cols[0], y=numeric_cols[1], 
                        title=f'Relationship between {numeric_cols[0]} and {numeric_cols[1]}')
            fig.update_layout(uirevision='constant')  # Prevent refresh on interaction
            st.plotly_chart(fig, use_container_width=True)
        else:
            # Just a simple bar chart
            fig = px.bar(st.session_state.df, title='Data Overview')
            fig.update_layout(uirevision='constant')  # Prevent refresh on interaction
            st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.error(f"Visualization error: {str(e)}")
"""