# FILE: llm_handler.py

import os
import google.generativeai as genai
import pandas as pd
import io

# Configure the Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def generate_ai_summary(df: pd.DataFrame, kpis: dict) -> str:
    # This function remains unchanged.
    data_summary = df.head().to_string()
    buffer = io.StringIO()
    df.info(verbose=False, buf=buffer)
    schema_summary = buffer.getvalue()
    prompt = f"""
    You are an expert business analyst. Based on the following data summary, schema, and key performance indicators (KPIs), provide a concise executive summary for a business dashboard.
    **Instructions:**
    1.  Start with a one-sentence overall summary.
    2.  Highlight the top-performing product or region.
    3.  Point out any significant anomalies or opportunities.
    4.  Provide one key actionable recommendation.
    5.  Keep the entire summary under 400 words.
    **KPIs:**\n{kpis}
    **Data Schema:**\n{schema_summary}
    **Data Sample:**\n{data_summary}
    **Executive Summary:**
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating summary: {e}"


def generate_code_from_query(df: pd.DataFrame, history: list) -> str:
    """Translates a natural language query into Pandas code using Gemini, with conversation context."""
    schema = df.columns.tolist()

    unique_months = sorted(df['Month'].dt.strftime('%Y-%m').unique())
    latest_month = unique_months[-1] if unique_months else "N/A"
    previous_month = unique_months[-2] if len(unique_months) > 1 else "N/A"

    formatted_history = ""
    for message in history:
        role = "User" if message['role'] == 'user' else "Assistant"
        formatted_history += f"{role}: {message['content']}\n"
    
    # --- MODIFIED AND IMPROVED PROMPT ---
    prompt = f"""
    You are a Python code generation assistant for Pandas. Your task is to convert a user's question into a single, executable line of Python code by choosing the correct tool.

    **TOOL INSTRUCTIONS:**
    1.  **For standard data questions:** (e.g., "what is the total sales", "which product is best") Generate pandas code that results in a string, number, or table.
    2.  **For plotting/charting:** If the question starts with "Plot" (case-insensitive), you MUST call the `plot_to_base64()` tool.
    3.  **For forecasting/prediction:** If the question contains words like "forecast", "predict", or "project", you MUST call the `get_forecast()` tool.

    **CONTEXT:**
    - The DataFrame is named `df`.
    - Available columns: {schema}.
    - The output MUST be a single-line Python expression.

    **ERROR HANDLING:**
    - If a question is ambiguous or cannot be answered, return: "Error: I cannot answer that question with the available data. Please try rephrasing."

    **EXAMPLES:**
    - User: "what is the total sales"
    - Assistant Code: `df['Sales'].sum()`

    - User: "Plot total sales by product"
    - Assistant Code: `plot_to_base64(df.groupby('Product')['Sales'].sum().plot(kind='bar', title='Total Sales by Product'))`

    - User: "Forecast sales for the next 6 months"
    - Assistant Code: `get_forecast(df, target_column='Sales', periods=6)`

    - User: "Can you predict how many units we will sell?"
    - Assistant Code: `get_forecast(df, target_column='Units Sold', periods=3)`

    - User: "Project our revenue for the next quarter"
    - Assistant Code: `get_forecast(df, target_column='Sales', periods=3)`

    **CONVERSATION HISTORY:**
    {formatted_history}

    **Assistant Code:**
    """
    try:
        response = model.generate_content(prompt)
        # Clean up the response to ensure it's pure code
        code = response.text.strip().replace("`", "").replace("python", "")
        return code
    except Exception as e:
        return f"Error: LLM failed to generate code. {e}"