# Creates Plotly charts
import pandas as pd
import plotly.express as px
import plotly.io as pio

# Set a professional, dark theme for charts
pio.templates.default = "plotly_dark"

def create_charts(df: pd.DataFrame) -> dict:
    """Creates a dictionary of Plotly charts as JSON strings."""
    charts = {}

    # 1. Sales by Product (bar)
    sales_by_product = df.groupby('Product')['Sales'].sum().reset_index().sort_values('Sales', ascending=False)
    fig1 = px.bar(sales_by_product, x='Product', y='Sales', title="Total Sales by Product",
                  labels={'Sales': 'Total Sales ($)', 'Product': 'Product Name'})
    charts['sales_by_product'] = fig1.to_json()

    # 2. Sales by Region (pie)
    sales_by_region = df.groupby('Region')['Sales'].sum().reset_index().sort_values('Sales', ascending=False)
    fig2 = px.pie(sales_by_region, names='Region', values='Sales', title="Sales Distribution by Region", hole=0.3)
    charts['sales_by_region'] = fig2.to_json()

    # 3. Customer Satisfaction vs. Units Sold (scatter)
    fig3 = px.scatter(df, x='Units Sold', y='Customer Satisfaction', color='Product',
                      size='Sales', hover_name='Region', title="Satisfaction vs. Units Sold",
                      labels={'Units Sold': 'Units Sold', 'Customer Satisfaction': 'Customer Satisfaction (1-5)'})
    charts['satisfaction_vs_units'] = fig3.to_json()

    # 4. Units Sold by Region and Product (stacked bar)
    units_by_region_product = df.groupby(['Region', 'Product'])['Units Sold'].sum().reset_index()
    fig4 = px.bar(units_by_region_product, x='Region', y='Units Sold', color='Product',
                  title="Units Sold by Region and Product", barmode='stack',
                  labels={'Units Sold': 'Units Sold', 'Region': 'Region'})
    charts['units_by_region_product'] = fig4.to_json()

    # 5. Average Customer Satisfaction by Product (bar)
    avg_satisfaction_product = df.groupby('Product')['Customer Satisfaction'].mean().reset_index().sort_values('Customer Satisfaction', ascending=False)
    fig5 = px.bar(avg_satisfaction_product, x='Product', y='Customer Satisfaction',
                  title="Average Customer Satisfaction by Product",
                  labels={'Customer Satisfaction': 'Average Satisfaction (1-5)', 'Product': 'Product'})
    charts['avg_satisfaction_by_product'] = fig5.to_json()

    # 6. Sales vs Units Sold Scatter Plot (by Product)
    fig6 = px.scatter(df, x='Units Sold', y='Sales', color='Product',
                      hover_name='Region', title="Sales vs Units Sold by Product",
                      labels={'Units Sold': 'Units Sold', 'Sales': 'Sales ($)'})
    charts['sales_vs_units_scatter'] = fig6.to_json()

    # 7. Sales Efficiency Heatmap (Sales per Unit Sold) by Region and Product
    df['Sales per Unit'] = df['Sales'] / df['Units Sold']
    sales_efficiency = df.groupby(['Region', 'Product'])['Sales per Unit'].mean().reset_index()
    fig7 = px.density_heatmap(sales_efficiency, x='Region', y='Product', z='Sales per Unit',
                             color_continuous_scale='Viridis',
                             title="Sales Efficiency (Sales per Unit Sold) by Region and Product",
                             labels={'Sales per Unit': 'Sales per Unit Sold ($)'})
    charts['sales_efficiency_heatmap'] = fig7.to_json()

    return charts
