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

def generate_insurance_pdf(farmer_name, contact, policy_num, contract_address, issue_date, coverage_amount, premium_amount, start_date, end_date, policy_type, insurer_name="AgriSure Insurance"):
    """Generate a detailed insurance certificate PDF"""
    buffer = io.BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72,
        title=f"Insurance Certificate - {policy_num}"
    )
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=1)) 
    styles.add(ParagraphStyle(name='Right', alignment=2))
    # Don't re-add Title and Subtitle styles that already exist
    # styles.add(ParagraphStyle(name='Title', fontSize=18, alignment=1, spaceAfter=12))  # Remove this line
    # styles.add(ParagraphStyle(name='Subtitle', fontSize=14, alignment=1, spaceAfter=10))  # Remove this line

    # Instead, modify the existing Title style if needed
    styles['Title'].alignment = 1
    styles['Title'].spaceAfter = 12
    styles['Title'].fontSize = 18

    # Add only the custom heading style that doesn't exist
    styles.add(ParagraphStyle(name='Heading', fontSize=12, alignment=0, spaceAfter=6, fontName='Helvetica-Bold'))
    
    # Get logo from assets folder
    logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'logo.png')
    
    # Header section with logo and title
    header_data = [[]]
    
    try:
        # Add logo to document if it exists
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=1.5*inch, height=1.5*inch)
            header_data[0].append(logo)
        else:
            # Fallback text if logo not found
            header_data[0].append(Paragraph("<font size=12>AgriSure</font>", styles['Center']))
            print(f"Logo file not found at: {logo_path}")
    except Exception as e:
        print(f"Error loading logo: {str(e)}")
        header_data[0].append(Paragraph("<font size=12>AgriSure</font>", styles['Center']))
    
    # Add titles next to logo
    title_cell = []
    title_cell.append(Paragraph("<font size=18>AGRI INSURE BLOCKCHAIN</font>", styles['Center']))
    title_cell.append(Paragraph("<font size=14>Insurance Certificate</font>", styles['Center']))
    title_cell.append(Paragraph(f"<font size=10>Policy: {policy_num}</font>", styles['Center']))
    header_data[0].append(title_cell)
    
    # Create header table
    header_table = Table(header_data, colWidths=[2*inch, 3.5*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('ALIGN', (1, 0), (1, 0), 'LEFT'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 20))
    
    # Policy details section
    elements.append(Paragraph("POLICY DETAILS", styles['Heading']))
    elements.append(Spacer(1, 5))
    
    # Format dates for display
    formatted_start_date = start_date if isinstance(start_date, str) else start_date.strftime("%B %d, %Y")
    formatted_end_date = end_date if isinstance(end_date, str) else end_date.strftime("%B %d, %Y")
    
    # Format currency values
    formatted_coverage = f"₹ {float(coverage_amount):,.2f}"
    formatted_premium = f"₹ {float(premium_amount):,.2f}"
    
    # Main details table
    policy_data = [
        ["Farmer Name:", farmer_name, "Policy Number:", policy_num],
        ["Contact:", contact, "Policy Type:", policy_type.replace('_', ' ').title() if isinstance(policy_type, str) else str(policy_type)],
        ["Coverage Amount:", formatted_coverage, "Premium Amount:", formatted_premium],
        ["Start Date:", formatted_start_date, "End Date:", formatted_end_date],
        ["Issued On:", issue_date, "Insurer:", insurer_name],
    ]
    
    # Create table
    policy_table = Table(policy_data, colWidths=[1.5*inch, 1.8*inch, 1.5*inch, 1.8*inch])
    policy_table.setStyle(TableStyle([
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('BACKGROUND', (2, 0), (2, -1), colors.lightgrey),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    elements.append(policy_table)
    elements.append(Spacer(1, 20))
    
    # Blockchain verification section
    elements.append(Paragraph("BLOCKCHAIN VERIFICATION", styles['Heading']))
    elements.append(Spacer(1, 5))
    
    blockchain_data = [
        ["Contract Address:", contract_address],
        ["Verification Status:", "Verified on Blockchain"],
        ["Timestamp:", datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")]
    ]
    
    blockchain_table = Table(blockchain_data, colWidths=[2*inch, 4.6*inch])
    blockchain_table.setStyle(TableStyle([
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    elements.append(blockchain_table)
    
    # Terms and conditions section
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("TERMS & CONDITIONS", styles['Heading']))
    elements.append(Spacer(1, 5))
    terms_text = """
    1. This policy is subject to the terms and conditions mentioned in the policy document.
    2. Claims must be filed within 30 days of the loss incident.
    3. The policy is valid only for the duration mentioned above.
    4. Policy verification can be done by scanning the QR code or using the contract address on AgriSure portal.
    5. Premium amount is non-refundable except as per the cancellation policy.
    """
    elements.append(Paragraph(terms_text, styles['Normal']))
    
    # Footer
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("This certificate is digitally generated on Blockchain for insurance verification purposes.", 
                             styles['Center']))
    elements.append(Paragraph(f"Document ID: {uuid.uuid4().hex[:16].upper()}", styles['Center']))
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
            issue_date=datetime.now().strftime("%Y-%m-%d"),
            coverage_amount=coverage_amount,
            premium_amount=premium_amount,
            start_date=start_date,
            end_date=end_date,
            policy_type=policy_type
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
        issue_date=policy.created_at.strftime("%Y-%m-%d") if policy.created_at else datetime.now().strftime("%Y-%m-%d"),
        coverage_amount=policy.coverage_amount,
        premium_amount=policy.premium_amount,
        start_date=policy.start_date,
        end_date=policy.end_date,
        policy_type=policy.policy_type
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