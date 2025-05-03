from flask import Blueprint, request, jsonify, send_file
from database import SessionLocal
from models.insurancePolicy import InsPolicy, PolicyStatusEnum
from models.farmer import Farmer
from datetime import datetime
from utils.auth import token_required, farmer_required
import io
import base64
import os
import uuid
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

insurance_bp = Blueprint("farmer_insurance_bp", __name__, url_prefix="/api/v1/insurance")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def generate_insurance_pdf(farmer_name, contact, policy_num, contract_address, issue_date):
    """Generate an insurance certificate PDF without saving to disk"""
    buffer = io.BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=1))
    
    # Title
    elements.append(Paragraph("<font size=18>AGRI INSURE BLOCKCHAIN</font>", styles['Center']))
    elements.append(Paragraph("<font size=14>Insurance Certificate</font>", styles['Center']))
    elements.append(Spacer(1, 20))
    
    # Information
    data = [
        ["Farmer Name:", farmer_name],
        ["Contact:", contact],
        ["Policy No.:", policy_num],
        ["Contract Address:", contract_address],
        ["Issued On:", issue_date]
    ]
    
    # Create table
    table = Table(data, colWidths=[2*inch, 3*inch])
    table.setStyle(TableStyle([
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey)
    ]))
    elements.append(table)
    
    # Footer
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("This certificate is digitally generated on Blockchain for insurance verification purposes.", styles['Center']))
    elements.append(Paragraph("Verified & Powered by Agri DApp Hackathon 2025", styles['Center']))
    
    # Build PDF
    doc.build(elements)
    
    # Return PDF bytes
    buffer.seek(0)
    return buffer.getvalue()

@insurance_bp.route("/buy-policy", methods=["POST"])
@token_required
@farmer_required
def buy_policy():
    db = next(get_db())

    email = request.user.get("email")
    if not email:
        return jsonify({"error": "Email not found in session"}), 403

    farmer = db.query(Farmer).filter_by(email=email).first()
    if not farmer or not farmer.aadhaar_number:
        return jsonify({"error": "Farmer not found or Aadhaar missing"}), 404

    aadhaar_number = farmer.aadhaar_number

    data = request.json
    policy_num = data.get("policy_num")
    coverage_amount = data.get("coverage_amount")
    premium_amount = data.get("premium_amount")
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    insurer_id = data.get("insurer_id")
    policy_type = data.get("policy_type", "basic")
    location = data.get("location")
    crop_type = data.get("cropType")
    landsize = data.get("landSize")

    if not all([policy_num, coverage_amount, premium_amount, start_date, end_date, insurer_id]):
        return jsonify({"error": "Missing one or more required fields"}), 400

    try:
        coverage_amount = float(coverage_amount)
        premium_amount = float(premium_amount)
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        landsize = float(landsize) if landsize else 0
        
        new_policy = InsPolicy(
            policy_num=policy_num,
            aadhaar_number=aadhaar_number,
            coverage_amount=coverage_amount,
            premium_amount=premium_amount,
            start_date=start_date,
            end_date=end_date,
            status="active",
            policy_type=policy_type,
            created_at=datetime.now(),
            insurer_id=insurer_id
        )

        db.add(new_policy)
        db.commit()

        # Generate a mock blockchain contract address
        contract_address = "0x" + uuid.uuid4().hex[:40]
        
        # Generate insurance certificate PDF without saving to disk
        pdf_bytes = generate_insurance_pdf(
            farmer_name=farmer.full_name,
            contact=farmer.phone,
            policy_num=policy_num,
            contract_address=contract_address,
            issue_date=datetime.now().strftime("%Y-%m-%d")
        )
        
        # Convert PDF to base64 for frontend
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        
        # Create filename for frontend (this won't be saved on server)
        pdf_filename = f"Insurance_{farmer.full_name.replace(' ', '_')}_{policy_num}.pdf"

        return jsonify({
            "message": "Insurance policy purchased successfully",
            "policy_num": new_policy.policy_num,
            "status": new_policy.status.value,
            "pdf_certificate": pdf_base64,
            "pdf_filename": pdf_filename
        }), 201

    except Exception as e:
        db.rollback()
        return jsonify({"error": "Policy purchase failed", "detail": str(e)}), 500


@insurance_bp.route("/certificate/<policy_num>", methods=["GET"])
@token_required
@farmer_required
def get_certificate(policy_num):
    db = next(get_db())
    
    email = request.user.get("email")
    if not email:
        return jsonify({"error": "Email not found in session"}), 403
        
    farmer = db.query(Farmer).filter_by(email=email).first()
    if not farmer:
        return jsonify({"error": "Farmer not found"}), 404
        
    # Find the policy
    policy = db.query(InsPolicy).filter_by(
        policy_num=policy_num, 
        aadhaar_number=farmer.aadhaar_number
    ).first()
    
    if not policy:
        return jsonify({"error": "Policy not found or not authorized"}), 404
        
    # Generate the certificate on the fly
    contract_address = "0x" + uuid.uuid4().hex[:40]  # Mock address
    pdf_bytes = generate_insurance_pdf(
        farmer_name=farmer.full_name,
        contact=farmer.phone,
        policy_num=policy_num,
        contract_address=contract_address,
        issue_date=policy.created_at.strftime("%Y-%m-%d") if policy.created_at else datetime.now().strftime("%Y-%m-%d")
    )
    
    # Create a file-like object from PDF bytes
    pdf_io = io.BytesIO(pdf_bytes)
    pdf_io.seek(0)
    
    return send_file(
        pdf_io,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"Insurance_{farmer.full_name.replace(' ', '_')}_{policy_num}.pdf"
    )