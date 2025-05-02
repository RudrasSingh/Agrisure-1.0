from flask import Blueprint, request, send_file, jsonify
from datetime import datetime
import io
from backend.database import get_db  # your SQLAlchemy session generator
from models import Claim  # your SQLAlchemy model
from models.lands import LandData  # your SQLAlchemy model for land data
from utils.area_converter import convert_to_sq_meters
from utils.sentinel import generate_bbox
from utils.analytics import analyze_indices
from utils.generate import generate_narrative, build_pdf_report
from sqlalchemy.orm import Session

bp = Blueprint("satelliteVerification", __name__, url_prefix="/api/v1/satellite")

@bp.route("/verify/<int:claim_id>", methods=["GET"])
def verify(claim_id):
    db: Session = next(get_db())
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        return jsonify({"error": "Claim not found"}), 404

    # Fetch land data using Aadhaar number from the claim
    land_data = db.query(LandData).filter_by(aadhaar_number=claim.aadhaar_number).first()
    if not land_data:
        return jsonify({"error": "Land data not found for the given Aadhaar number"}), 404

    # 1. Prepare inputs
    lat, lon = land_data.coordinates["latitude"], land_data.coordinates["longitude"]
    area_sqm = land_data.area_hec * 10000  # Convert acres to square meters
    bbox = generate_bbox(lat, lon, area_sqm)
    geometry = None  # or construct from bbox/polygon
    # Compute dimensions
    from sentinelhub import bbox_to_dimensions
    size = bbox_to_dimensions(bbox, resolution=10)

    # 2. Analyze
    end_date = datetime.now()
    analysis = analyze_indices(bbox, geometry, end_date, size)

    # 3. Narrative & PDF
    narrative = generate_narrative(analysis)
    farmer_info = {
        "Latitude": lat,
        "Longitude": lon,
        "Area": f"{land_data.area_hec} acres",
        "Crop Type": land_data.crop_type,
        "Sowing Date": land_data.sowing_date.isoformat() if land_data.sowing_date else "N/A",
        "Soil Type": land_data.soil_type
    }
    pdf_bytes = build_pdf_report(farmer_info, analysis, narrative)

    # 4. Return PDF + confidence
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"AgriSure_Report_{claim.id}.pdf",
        headers={"X-Confidence-Score": f"{analysis['confidence']:.2f}"}
    )
