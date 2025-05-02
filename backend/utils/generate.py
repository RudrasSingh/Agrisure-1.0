import os
import base64
from fpdf import FPDF
import google.generativeai as genai
from datetime import datetime

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def generate_narrative(timeseries_data: dict) -> str:
    """
    Uses Gemini to produce a human-readable summary of the NDVI/NDMI/GNDVI trends.
    """
    prompt = (
        "Provide a concise farm health report based on these time series:\n\n"
        f"NDVI (20d): {timeseries_data['series_20d']['ndvi']}\n"
        f"NDMI (20d): {timeseries_data['series_20d']['ndmi']}\n"
        f"GNDVI (20d): {timeseries_data['series_20d']['gndvi']}\n\n"
        "Identify key declines or improvements and relate to possible crop stress or damage."
    )
    model = genai.GenerativeModel("gemini-2.0-flash")
    resp = model.generate_content(prompt)
    return resp.text

def build_pdf_report(farmer_info: dict, analysis: dict, narrative: str) -> bytes:
    """
    Combines images, plots, narrative, and key stats into a PDF.
    Returns PDF as bytes.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(True, margin=15)
    # Cover
    pdf.add_page()
    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 10, "AgriSure Farm Health Report", ln=True, align="C")
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", ln=True, align="C")

    # Farmer info
    pdf.ln(10)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "Farm Details", ln=True)
    pdf.set_font("Arial", "", 12)
    for k,v in farmer_info.items():
        pdf.cell(0, 6, f"{k}: {v}", ln=True)

    # Narrative
    pdf.ln(8)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "Executive Summary", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 6, narrative)

    # Plots
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "Trends (20 days)", ln=True)
    for key, b64 in analysis["plots"].items():
        if key.endswith("_20d"):
            img_data = base64.b64decode(b64)
            with open(f"/tmp/{key}.png", "wb") as f:
                f.write(img_data)
            pdf.image(f"/tmp/{key}.png", w=180)
            pdf.ln(5)

    # Confidence
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 6, f"Confidence Score: {analysis['confidence']:.2f}", ln=True)

    return pdf.output(dest="S").encode("latin1")
