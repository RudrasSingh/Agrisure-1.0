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
        "AgriSure Farm Monitoring Report for Insurance Claim Review\n\n"
    f"Analyzing vegetation health within farm boundaries: {coords}\n"
    "Objective: Provide a clear and concise, branded summary of the 31-day daily average NDVI trends. This summary should highlight key changes in vegetation health relevant to a potential insurance claim, explained in a way that is easy for both insurance adjusters and farmers to understand.\n\n"
    f"Daily Average NDVI over the past 31 days:\n{stats_text}\n\n"
    "Instructions:\n"
    "1. **Key Trend Identification:** Briefly identify the most important trends in the NDVI data over the 31-day period. Focus on significant increases, decreases, or consistently low values.\n"
    "2. **Plain Language Explanation:** Explain what these NDVI trends likely mean for the health of the crops in simple, non-technical terms. Avoid jargon related to satellite data.\n"
    "3. **Insurance Relevance (if applicable):** If the data suggests a decline or anomaly relevant to an insurance claim, clearly state this connection in an understandable way (e.g., 'The significant drop in vegetation health starting around [date] may indicate damage relevant to your claim.').\n"
    "4. **AgriSure Branding:** Maintain a professional and trustworthy tone, reinforcing AgriSure's role in providing clear agricultural insights.\n"
    "5. **Concise Summary:** Keep the analysis brief and to the point, focusing on the most critical information. Aim for a 'quick read' that conveys the essential findings effectively.\n"
    "6. **Visual Analogy (Optional but helpful):** If possible, use simple analogies to explain NDVI changes (e.g., 'Think of NDVI like a plant's 'greenness score.' A high score means healthy, while a low score suggests stress.').\n\n"
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
