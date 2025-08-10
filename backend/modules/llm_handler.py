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
    
    # --- NEW, ADVANCED PROMPT ---
    prompt = f"""
    You are an expert Python data analyst. Your job is to convert a user's question into a single, executable line of Python code to query a pandas DataFrame.

    **PERSONA & RULES:**
    1.  **You are the Decision Maker:** Analyze the user's intent. Do they want a specific number, a table, a plot, or a forecast? Choose the best tool for the job.
    2.  **Combine Filters:** Users will often ask for multiple things at once (e.g., "sales for product A in the South region last month"). Your code must combine all filters correctly.
    3.  **Handle Ambiguity:** If a term is vague (e.g., "best product"), make a reasonable assumption (e.g., highest sales) and state it in your answer. Do not just error out.
    4.  **Code Only:** Your output MUST be ONLY the single line of Python code and nothing else.

    **AVAILABLE TOOLS & CONTEXT:**
    - DataFrame is named `df`.
    - Columns are: {schema}.
    - Use `plot_to_base64()` for any visual chart/graph/plot requests.
    - Use `get_forecast()` for any prediction/forecast/projection requests. This tool can now take a `filters` dictionary.
    - Relative Dates: 'last month' means '{previous_month}', 'latest month' means '{latest_month}'.
    - Date Format: For specific dates like "in November 2024" or "on 11-2024", use the filter `df['Month'].dt.strftime('%Y-%m') == '2024-11'`.

    **ADVANCED EXAMPLES (How to Think):**

    - User: "Plot me a graph product wise for last month"
      - Intent: Plotting. Filters: 'last month'.
      - Assistant Code: `plot_to_base64(df[df['Month'].dt.strftime('%Y-%m') == '{previous_month}'].groupby('Product')['Sales'].sum().plot(kind='bar', title='Sales by Product for {previous_month}'))`

    - User: "what product is sold more at 11th month 2024"
      - Intent: Data retrieval. Filters: '11-2024'. Assumption: "sold more" means by 'Sales'.
      - Assistant Code: `df[df['Month'].dt.strftime('%Y-%m') == '2024-11'].groupby('Product')['Sales'].sum().idxmax()`

    - User: "what is the sales of product b last month"
      - Intent: Data retrieval. Filters: 'Product B', 'last month'.
      - Assistant Code: `df[(df['Product'] == 'Product B') & (df['Month'].dt.strftime('%Y-%m') == '{previous_month}')]['Sales'].sum()`

    - User: "Forecast sales for the next 3 months for product a"
      - Intent: Forecasting with a filter.
      - Assistant Code: `get_forecast(df, target_column='Sales', periods=3, filters={{'Product': 'Product A'}})`

    - User: "show me the best performing product"
      - Intent: Data retrieval. Ambiguity: "best performing". Assumption: by total sales.
      - Assistant Code: `df.groupby('Product')['Sales'].sum().idxmax()`

    **CONVERSATION HISTORY:**
    {formatted_history}

    **Assistant Code:**
    """
    try:
        response = model.generate_content(prompt)
        code = response.text.strip().replace("`", "").replace("python", "")
        return code
    except Exception as e:
        return f"Error: LLM failed to generate code. {e}"