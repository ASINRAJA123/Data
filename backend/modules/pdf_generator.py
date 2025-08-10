from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa
import pandas as pd
import plotly.io as pio
import io
import base64
from datetime import datetime

def create_pdf_report(kpis: dict, summary: str, charts: dict, df: pd.DataFrame) -> bytes:
    """Renders an HTML template with data and converts it to a PDF using xhtml2pdf."""
    # --- THIS IS THE FIX ---
    # The path must go up one level from /backend to find the /templates folder.
    env = Environment(loader=FileSystemLoader('../templates'))
    # --- END OF FIX ---
    
    template = env.get_template('report_template.html')

    # Convert Plotly JSON charts to static images (base64) for the PDF
    img_charts = {}
    for key, chart_json in charts.items():
        fig = pio.from_json(chart_json)
        img_bytes = fig.to_image(format="png", scale=2)
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        img_charts[key] = f"data:image/png;base64,{img_base64}"

    # Prepare a sample of the data for the PDF
    data_sample_html = df.head(10).to_html(classes='data-table', index=False)
    
    # Render the HTML template with all the data
    html_out = template.render(
        kpis=kpis,
        summary=summary,
        charts=img_charts,
        data_sample_html=data_sample_html,
        now=datetime.now
    )
    
    # --- PDF Conversion Logic ---
    result = io.BytesIO()

    pdf = pisa.CreatePDF(
        src=io.StringIO(html_out),
        dest=result
    )
    
    if pdf.err:
        # We can add more detailed logging here if needed
        print(f"xhtml2pdf error: {pdf.err}")
        raise Exception("Error generating PDF")

    return result.getvalue()