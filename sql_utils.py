import os
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

endpoint = "https://aihubtsprova4768698776.cognitiveservices.azure.com/openai/deployments/gpt-4o-mini"
model_name = "gpt-4o-mini"

AZURE_KEY = os.getenv("AZURE_KEY")
client = ChatCompletionsClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(AZURE_KEY),
)

def generate_sql_query(user_question, schema_info=None):
    """
    Use Azure's ChatCompletionsClient to transform the user question into a valid SQL query.
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
