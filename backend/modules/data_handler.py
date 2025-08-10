# Cleans and manages the dataset
import pandas as pd
import io
import os # <-- NEW: Import the 'os' module to check for files

# --- NEW: Define a path for our temporary storage ---
# This will create a 'temp_storage' folder inside your 'backend' directory
TEMP_STORAGE_DIR = "temp_storage"
TEMP_DATA_PATH = os.path.join(TEMP_STORAGE_DIR, "current_data.csv")
# ----------------------------------------------------

# In-memory storage for the dataframe (acts as a quick cache).
df_storage = {}

def load_and_clean_data(file_content: bytes, filename: str) -> pd.DataFrame:
    """Loads data from file bytes, cleans it, saves it to a temp file, and returns a DataFrame."""
    try:
        # Create the temp directory if it doesn't exist
        os.makedirs(TEMP_STORAGE_DIR, exist_ok=True) # <-- NEW

        if filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(file_content))
        elif filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(io.BytesIO(file_content))
        else:
            raise ValueError("Unsupported file type")

        # --- Data Cleaning Pipeline ---
        if 'Month' in df.columns:
            df['Month'] = pd.to_datetime(df['Month'], errors='coerce')

        for col in ['Sales', 'Units Sold', 'Customer Satisfaction']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        for col in df.select_dtypes(include=['number']).columns:
            if df[col].isnull().any():
                df[col].fillna(df[col].mean(), inplace=True)
        
        # NOTE: We keep dropna to ensure the saved data is always clean.
        df.dropna(subset=['Region', 'Product', 'Month'], inplace=True)

        # --- NEW: Save the cleaned data to disk and also cache in memory ---
        df.to_csv(TEMP_DATA_PATH, index=False)
        df_storage['current'] = df
        # -----------------------------------------------------------------
        
        return df
    except Exception as e:
        print(f"Error processing file: {e}")
        raise

def get_dataframe() -> pd.DataFrame:
    """
    Retrieves the DataFrame. Tries memory first, then disk, otherwise raises error.
    """
    # 1. Try to get from the fast in-memory cache
    if 'current' in df_storage:
        return df_storage['current']

    # 2. If not in memory, try to load from the disk file (after a server restart)
    if os.path.exists(TEMP_DATA_PATH):
        print("Loading data from temporary file...") # Log for debugging
        # When reading from CSV, we must tell pandas to parse the 'Month' column as a date again
        df = pd.read_csv(TEMP_DATA_PATH, parse_dates=['Month'])
        # Put it back into memory for the next request
        df_storage['current'] = df
        return df

    # 3. If it's not in memory or on disk, then no data has been uploaded yet.
    raise ValueError("No data has been uploaded yet.")