from flask import Blueprint, request, send_file, jsonify
from datetime import datetime
import io
from backend.database import get_db  # your SQLAlchemy session generator
from models import Claim  # your SQLAlchemy model
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

    # 1. Prepare inputs
    lat, lon = claim.latitude, claim.longitude
    area_sqm = convert_to_sq_meters(claim.area_value, claim.area_unit)
    bbox = generate_bbox(lat, lon, area_sqm)
    geometry = None  # or construct from bbox/polygon
    # compute dimensions
    from sentinelhub import bbox_to_dimensions
    size = bbox_to_dimensions(bbox, resolution=10)

    # 2. Analyze
    end_date = datetime.utcnow().date()
    analysis = analyze_indices(bbox, geometry, end_date, size)

    # 3. Narrative & PDF
    narrative = generate_narrative(analysis)
    farmer_info = {
        "Latitude": lat,
        "Longitude": lon,
        "Area": f"{claim.area_value} {claim.area_unit}"
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
