# FILE: app.py

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
from dotenv import load_dotenv

# --- NEW IMPORTS FOR PLOTTING ---
import io
import base64
import matplotlib
matplotlib.use('Agg') # Use a non-interactive backend for server environments
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA

# ---------------------------------

# Load environment variables from .env file
load_dotenv()

# Import our custom modules
from modules import data_handler, insights_generator, chart_generator, llm_handler, pdf_generator

app = FastAPI()

chat_history = []

# --- NEW HELPER FUNCTION FOR PLOTTING ---
def plot_to_base64(plot_obj):
    """
    Takes a Matplotlib Axes object, saves it to a buffer,
    and returns a Base64 encoded string in a structured dictionary.
    """
    fig = plot_obj.get_figure()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig) # Close the figure to free up memory
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    return {"type": "plot", "image": image_base64}
# ------------------------------------------

def get_forecast(df: pd.DataFrame, target_column: str = 'Sales', periods: int = 3):
    """
    Generates a forecast using a simple ARIMA model.
    Returns the forecast as a formatted string.
    """
    try:
        # Ensure the 'Month' column is a datetime type for time series analysis
        if not pd.api.types.is_datetime64_any_dtype(df['Month']):
            return "Error: Forecasting requires a datetime 'Month' column."
            
        # Prepare the data: create a monthly time series of the target column
        time_series = df.groupby('Month')[target_column].sum().asfreq('MS')

        if len(time_series) < 12:
            return "Error: Not enough historical data (at least 12 months required) to generate a reliable forecast."
        
        # Fit a simple ARIMA model (AutoRegressive Integrated Moving Average)
        # order(p,d,q): p=lags, d=differencing, q=moving average window. (1,1,1) is a common baseline.
        model = ARIMA(time_series, order=(1, 1, 1))
        model_fit = model.fit()
        
        # Generate the forecast for the next 'periods' months
        forecast_result = model_fit.forecast(steps=periods)
        
        # Format the output nicely
        forecast_df = forecast_result.reset_index()
        forecast_df.columns = ['Forecasted Month', f'Predicted {target_column}']
        forecast_df['Forecasted Month'] = forecast_df['Forecasted Month'].dt.strftime('%Y-%m')
        forecast_df[f'Predicted {target_column}'] = forecast_df[f'Predicted {target_column}'].round(2)
        
        return f"Here is the forecast for the next {periods} months:\n\n{forecast_df.to_string(index=False)}"

    except Exception as e:
        return f"Error: Failed to generate forecast. The model may not be suitable for this data. Details: {e}"
# ----------------------------------------------



@app.on_event("startup")
async def startup_event():
    print("Application startup: attempting to preload data...")
    try:
        data_handler.get_dataframe()
        print("Preload successful: Data is ready.")
    except ValueError:
        print("No pre-existing data found. Waiting for upload.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

@app.post("/api/upload")
async def upload_data(file: UploadFile = File(...)):
    # This endpoint is correct and remains unchanged from your old code
    try:
        contents = await file.read()
        data_handler.load_and_clean_data(contents, file.filename)
        global chat_history
        chat_history.clear()
        return JSONResponse(content={"message": "File uploaded and processed successfully."})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

@app.get("/api/dashboard")
async def get_dashboard_data():
    # This endpoint is correct and remains unchanged from your old code
    try:
        df = data_handler.get_dataframe()
        kpis = insights_generator.generate_kpis(df)
        charts = chart_generator.create_charts(df)
        ai_summary = llm_handler.generate_ai_summary(df, kpis)
        return {"kpis": kpis, "charts": charts, "summary": ai_summary}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


# --- MODIFIED CHAT ENDPOINT ---
@app.post("/api/chat")
async def chat_with_data(request: ChatRequest):
    try:
        df = data_handler.get_dataframe()
        global chat_history

        chat_history.append({"role": "user", "content": request.message})
        
        MAX_HISTORY = 10
        recent_history = chat_history[-MAX_HISTORY:]

        code_to_execute = llm_handler.generate_code_from_query(df, recent_history)
        
        if code_to_execute.startswith("Error:"):
            chat_history.append({"role": "bot", "content": code_to_execute})
            # Return a structured response for the frontend
            return {"answer": code_to_execute, "type": "text"}

        # Define the execution environment, making our helper available
        exec_globals = {
            "pd": pd,
            "df": df,
            "plot_to_base64": plot_to_base64,
            "get_forecast": get_forecast # Make the forecast function available
        }
        
        # Execute the code generated by the LLM
        result = eval(code_to_execute, exec_globals)
        
        # Check if the result is a plot
        if isinstance(result, dict) and result.get("type") == "plot":
            # If it's a plot, the result is already in the correct JSON format.
            answer_for_history = "Here is the plot you requested."
            chat_history.append({"role": "bot", "content": answer_for_history})
            return result
        
        # If not a plot, handle as a normal data/text response
        if isinstance(result, (pd.DataFrame, pd.Series)):
            answer = result.to_string()
        else:
            answer = str(result)
        
        chat_history.append({"role": "bot", "content": answer})
        # Return a structured response for the frontend
        return {"answer": answer, "type": "text"}
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"Chat execution error: {e}")
        error_message = f"An error occurred: {e}. I couldn't generate that. Please try rephrasing your request."
        chat_history.append({"role": "bot", "content": error_message})
        raise HTTPException(status_code=500, detail="Error executing the request.")


@app.get("/api/export-pdf")
async def export_pdf_report():
    # This endpoint is correct and remains unchanged from your old code
    try:
        df = data_handler.get_dataframe()
        kpis = insights_generator.generate_kpis(df)
        charts = chart_generator.create_charts(df)
        summary = llm_handler.generate_ai_summary(df, kpis)
        pdf_bytes = pdf_generator.create_pdf_report(kpis, summary, charts, df)
        return Response(content=pdf_bytes, media_type="application/pdf",
                        headers={"Content-Disposition": "attachment;filename=dashboard_report.pdf"})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")