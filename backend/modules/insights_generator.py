# Generates KPIs and text insights
import pandas as pd

def generate_kpis(df: pd.DataFrame) -> dict:
    """Generates key performance indicators from the DataFrame."""
    total_sales = df['Sales'].sum()
    total_units_sold = df['Units Sold'].sum()
    avg_satisfaction = df['Customer Satisfaction'].mean()
    
    return {
        "total_sales": f"${total_sales:,.0f}",
        "total_units_sold": f"{total_units_sold:,.0f}",
        "average_satisfaction": f"{avg_satisfaction:.2f} / 5"
    }

def find_anomalies_and_opportunities(df: pd.DataFrame) -> dict:
    """Identifies interesting patterns like anomalies and opportunities."""
    # Anomaly: High Sales, Low Satisfaction
    high_sales_threshold = df['Sales'].quantile(0.75)
    low_satisfaction_threshold = df['Customer Satisfaction'].quantile(0.25)
    
    anomaly = df[(df['Sales'] >= high_sales_threshold) & 
                 (df['Customer Satisfaction'] <= low_satisfaction_threshold)]

    # Opportunity: High Sales, High Satisfaction
    high_satisfaction_threshold = df['Customer Satisfaction'].quantile(0.75)
    opportunity = df[(df['Sales'] >= high_sales_threshold) & 
                     (df['Customer Satisfaction'] >= high_satisfaction_threshold)]

    return {
        "anomaly": anomaly.to_dict(orient='records'),
        "opportunity": opportunity.to_dict(orient='records')
    }