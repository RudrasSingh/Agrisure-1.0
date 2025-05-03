from flask import Blueprint, request, send_file, jsonify
from datetime import datetime, timedelta
import io, os
from backend.database import get_db  # your SQLAlchemy session generator
from models import Claim  # your SQLAlchemy model
from models.lands import LandData  # your SQLAlchemy model for land data
from utils.area_converter import convert_to_sq_meters
from utils.sentinel import generate_bbox
from utils.analytics import analyze_indices
from utils.generate import generate_narrative, build_pdf_report
from sqlalchemy.orm import Session
from backend.app import scheduler  # Import the scheduler

bp = Blueprint("satelliteVerification", __name__, url_prefix="/api/v1/satellite")

def process_verification(claim_id):
    """
    Background task to process satellite verification for a claim
    """
    with next(get_db()) as db:
        claim = db.query(Claim).filter(Claim.id == claim_id).first()
        if not claim:
            print(f"Error: Claim {claim_id} not found")
            return
            
        # Update claim status to "processing"
        claim.claim_sts = "processing"
        db.commit()
        
        # Fetch land data using Aadhaar number from the claim
        land_data = db.query(LandData).filter_by(aadhaar_number=claim.aadhaar_number).first()
        if not land_data:
            print(f"Error: Land data not found for claim {claim_id}")
            claim.claim_sts = "rejected"
            db.commit()
            return
            
        try:
            # 1. Prepare inputs
            lat, lon = land_data.coordinates["latitude"], land_data.coordinates["longitude"]
            area_sqm = land_data.area_hec * 10000  # Convert hectares to square meters
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
                "Area": f"{land_data.area_hec} hectares",
                "Crop Type": land_data.crop_type,
                "Sowing Date": land_data.sowing_date.isoformat() if land_data.sowing_date else "N/A",
                "Soil Type": land_data.soil_type
            }
            pdf_bytes = build_pdf_report(farmer_info, analysis, narrative)
            
            # 4. Save PDF to storage
            pdf_filename = f"AgriSure_Report_{claim_id}.pdf"
            upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
                
            pdf_path = os.path.join(upload_dir, pdf_filename)
            with open(pdf_path, 'wb') as f:
                f.write(pdf_bytes)
                
            # 5. Update claim with results
            claim.confidence_score = float(analysis['confidence'])
            
            # Determine if claim is valid based on confidence score
            if analysis['confidence'] > 0.7:  # Example threshold
                claim.claim_sts = "approved"
            else:
                claim.claim_sts = "rejected"
                claim.reason_ = narrative["conclusion"]
                
            claim.updated_at = datetime.now()
            db.commit()
            
            print(f"Successfully processed claim {claim_id} with confidence {analysis['confidence']}")
            
        except Exception as e:
            print(f"Error processing claim {claim_id}: {str(e)}")
            claim.claim_sts = "error"
            claim.reason_ = f"Processing error: {str(e)}"
            claim.updated_at = datetime.now()
            db.commit()

@bp.route("/verify/<int:claim_id>", methods=["GET"])
def verify(claim_id):
    """
    Manual verification endpoint - immediately processes the claim
    """
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
    area_sqm = land_data.area_hec * 10000  # Convert hectares to square meters
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
        "Area": f"{land_data.area_hec} hectares",
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


@bp.route("/schedule-verification/<int:claim_id>", methods=["POST"])
def schedule_verification(claim_id):
    """
    Schedule a verification job to run 24 hours after a claim is filed
    """
    db: Session = next(get_db())
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        return jsonify({"error": "Claim not found"}), 404
        
    # Check if claim is in a state that can be verified
    if claim.claim_sts not in ["pending", "submitted"]:
        return jsonify({"error": f"Claim is in '{claim.claim_sts}' state and cannot be scheduled for verification"}), 400
    
    # Calculate the run time (24 hours from now)
    run_time = datetime.now() + timedelta(hours=24)
    
    # Schedule the job with a unique ID based on the claim_id
    job_id = f"verify_claim_{claim_id}"
    
    # Remove any existing job with the same ID
    scheduler.remove_job(job_id, jobstore='default', ignore_if_not_exists=True)
    
    # Add the new job
    scheduler.add_job(
        process_verification, 
        'date', 
        run_date=run_time, 
        args=[claim_id], 
        id=job_id,
        replace_existing=True,
        jobstore='default'
    )
    
    # Update claim status
    claim.claim_sts = "scheduled"
    claim.updated_at = datetime.now()
    db.commit()
    
    return jsonify({
        "message": f"Verification for claim {claim_id} scheduled for {run_time}",
        "scheduled_time": run_time.isoformat(),
        "job_id": job_id
    }), 200


#automatically schedule verification after claim filing
def schedule_verification_after_filing(claim_id):
    """
    Helper function to be called when a new claim is filed
    """
    run_time = datetime.now() + timedelta(hours=24)
    job_id = f"verify_claim_{claim_id}"
    
    scheduler.add_job(
        process_verification, 
        'date', 
        run_date=run_time, 
        args=[claim_id], 
        id=job_id,
        replace_existing=True,
        jobstore='default'
    )
    
    print(f"Verification for claim {claim_id} scheduled for {run_time}")
    return job_id
