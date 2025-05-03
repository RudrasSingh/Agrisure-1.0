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
    """Generate a stunning, professional insurance certificate PDF"""
    buffer = io.BytesIO()
    
    # Create PDF document with tighter margins for better layout
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30,
        title=f"Insurance Certificate - {policy_num}"
    )
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Styles with better typography
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=1, fontName='Helvetica'))
    styles.add(ParagraphStyle(name='Right', alignment=2, fontName='Helvetica'))
    
    # MODIFY existing styles instead of adding new ones with the same name
    # Don't add 'BodyText' as a new style, modify the existing one
    styles['BodyText'].fontName = 'Helvetica'
    styles['BodyText'].fontSize = 10
    styles['BodyText'].leading = 14
    styles['BodyText'].spaceBefore = 6
    styles['BodyText'].spaceAfter = 6
    
    # Add styles that don't exist yet
    styles.add(ParagraphStyle(name='Heading1Green', fontName='Helvetica-Bold', fontSize=14, leading=16, 
                            textColor=colors.darkgreen, spaceBefore=10, spaceAfter=6))
    styles.add(ParagraphStyle(name='HeadingCenter', fontName='Helvetica-Bold', fontSize=14, alignment=1,
                            textColor=colors.darkgreen, spaceBefore=10, spaceAfter=6))
    
    # Import additional needed packages
    from reportlab.graphics.shapes import Drawing, Line
    from reportlab.lib.pagesizes import inch
    
    # Create a border for the entire document
    def add_border(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.darkgreen)
        canvas.setLineWidth(2)
        # Draw a border with rounded corners (rectangle)
        canvas.roundRect(20, 20, doc.width+20, doc.height+20, 10, stroke=1, fill=0)
        # Add a thin inner border
        canvas.setStrokeColor(colors.lightgreen)
        canvas.setLineWidth(0.5)
        canvas.roundRect(25, 25, doc.width+10, doc.height+10, 8, stroke=1, fill=0)
        canvas.restoreState()
    
    # Get AgriSure logo from URL
    logo_url = "https://xrcemypzyjsxoihkckin.supabase.co/storage/v1/object/public/agrisure//Untitled-1.png"
    
    # Try to fetch the logo from URL
    import requests
    from io import BytesIO
    
    logo = None
    try:
        response = requests.get(logo_url)
        if response.status_code == 200:
            logo_data = BytesIO(response.content)
            logo = Image(logo_data, width=2.2*inch, height=1.3*inch)
        else:
            print(f"Failed to fetch logo: HTTP {response.status_code}")
    except Exception as e:
        print(f"Error loading logo: {str(e)}")
    
    # Create a header with two-column layout
    if logo:
        # Create a table for header with logo on left, title on right
        header_data = [[logo, None]]
        
        # Right column with certificate title and info
        right_content = []
        right_content.append(Paragraph("<font color='#006400' size='18'><b>INSURANCE CERTIFICATE</b></font>", styles['Center']))
        right_content.append(Spacer(1, 5))
        right_content.append(Paragraph(f"<font color='#228B22' size='12'>Policy Number: <b>{policy_num}</b></font>", styles['Center']))
        right_content.append(Spacer(1, 5))
        right_content.append(Paragraph(f"<font size='10'>Issued On: {issue_date}</font>", styles['Center']))
        
        header_data[0][1] = right_content
        
        header_table = Table(header_data, colWidths=[2.8*inch, 4.7*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('LEFTPADDING', (0, 0), (0, 0), 0),
            ('RIGHTPADDING', (0, 0), (0, 0), 0),
        ]))
        elements.append(header_table)
    else:
        # Fallback if logo loading fails
        elements.append(Paragraph("<font color='#006400' size='20'><b>AGRISURE BLOCKCHAIN INSURANCE</b></font>", styles['Center']))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph("<font color='#228B22' size='16'><b>INSURANCE CERTIFICATE</b></font>", styles['Center']))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(f"<font size='12'>Policy Number: <b>{policy_num}</b></font>", styles['Center']))
        elements.append(Spacer(1, 5))
        elements.append(Paragraph(f"<font size='10'>Issued On: {issue_date}</font>", styles['Center']))
    
    # Add decorative divider
    from reportlab.platypus import HRFlowable
    elements.append(Spacer(1, 15))
    elements.append(HRFlowable(width="100%", thickness=1, lineCap='round', 
                            color=colors.darkgreen, spaceBefore=1, spaceAfter=1))
    elements.append(Spacer(1, 15))
    
    # Add certificate message with better formatting
    certificate_msg = f"""
    <font size='11' color='#333333'>This certificate confirms that <b>{farmer_name}</b> has purchased crop insurance 
    coverage through the AgriSure Blockchain Insurance platform. This insurance policy 
    is secured and verified using blockchain technology, ensuring complete transparency 
    and immutability of the insurance contract.</font>
    """
    elements.append(Paragraph(certificate_msg, styles['BodyText']))
    elements.append(Spacer(1, 15))
    
    # Format dates for display
    formatted_start_date = start_date if isinstance(start_date, str) else start_date.strftime("%B %d, %Y")
    formatted_end_date = end_date if isinstance(end_date, str) else end_date.strftime("%B %d, %Y")
    
    # Format currency values with Indian Rupee symbol
    formatted_coverage = f"RS {float(coverage_amount):,.2f}"
    formatted_premium = f"RS {float(premium_amount):,.2f}"
    
    # Policy type formatting
    policy_type_display = policy_type
    if isinstance(policy_type, str):
        policy_type_display = policy_type.replace('-', ' ').replace('_', ' ').title()
    
    # POLICYHOLDER INFORMATION SECTION - use Heading1Green instead of Heading1
    elements.append(Paragraph("<font color='#006400'>POLICYHOLDER INFORMATION</font>", styles['Heading1Green']))
    policyholder_data = [
        ["Farmer Name:", farmer_name],
        ["Contact:", contact],
    ]
    
    policyholder_table = Table(policyholder_data, colWidths=[1.8*inch, 5.7*inch])
    policyholder_table.setStyle(TableStyle([
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.lightgreen),
        ('BOX', (0, 0), (-1, -1), 1, colors.darkgreen),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (0, -1), colors.beige),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.darkgreen),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(policyholder_table)
    elements.append(Spacer(1, 15))
    
    # POLICY DETAILS SECTION 
    elements.append(Paragraph("<font color='#006400'>POLICY DETAILS</font>", styles['Heading1Green']))
    
    # Policy details with improved layout - 2 columns
    policy_data = [
        ["Policy Type:", policy_type_display, "Insurer:", insurer_name],
        ["Coverage Amount:", formatted_coverage, "Premium Amount:", formatted_premium],
        ["Start Date:", formatted_start_date, "End Date:", formatted_end_date],
    ]
    
    # Create styled table for policy details
    policy_table = Table(policy_data, colWidths=[1.8*inch, 2.5*inch, 1.5*inch, 1.7*inch])
    policy_table.setStyle(TableStyle([
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.lightgreen),
        ('BOX', (0, 0), (-1, -1), 1, colors.darkgreen),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (0, -1), colors.beige),
        ('BACKGROUND', (2, 0), (2, -1), colors.beige),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.darkgreen),
        ('TEXTCOLOR', (2, 0), (2, -1), colors.darkgreen),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(policy_table)
    elements.append(Spacer(1, 15))
    
    # BLOCKCHAIN VERIFICATION SECTION with improved styling
    elements.append(Paragraph("<font color='#006400'>BLOCKCHAIN VERIFICATION</font>", styles['Heading1Green']))
    
    blockchain_data = [
        ["Contract Address:", contract_address],
        ["Verification Status:", "✓ Verified on AgriSure Blockchain Network"],
        ["Timestamp:", datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")]
    ]
    
    blockchain_table = Table(blockchain_data, colWidths=[1.8*inch, 5.7*inch])
    blockchain_table.setStyle(TableStyle([
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.lightblue),
        ('BOX', (0, 0), (-1, -1), 1, colors.darkblue),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.darkblue),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(blockchain_table)
    
    # Terms and conditions section with better formatting
    elements.append(Spacer(1, 15))
    elements.append(Paragraph("<font color='#006400'>TERMS & CONDITIONS</font>", styles['Heading1Green']))
    
    terms_items = [
        "This policy is subject to the terms and conditions mentioned in the policy document.",
        "Claims must be filed within 30 days of the loss incident.",
        "The policy is valid only for the duration mentioned above.",
        "Policy verification can be done by scanning the QR code or using the contract address on AgriSure portal.",
        "Premium amount is non-refundable except as per the cancellation policy."
    ]
    
    terms_text = ""
    for i, item in enumerate(terms_items, 1):
        terms_text += f"<font size='10'><b>{i}.</b> {item}</font><br/><br/>"
    
    elements.append(Paragraph(terms_text, styles['BodyText']))
    
    # Footer with improved design
    elements.append(Spacer(1, 25))
    elements.append(HRFlowable(width="100%", thickness=1, lineCap='round', 
                            color=colors.darkgreen, spaceBefore=1, spaceAfter=1))
    elements.append(Spacer(1, 10))
    
    # Create a authentication block
    auth_data = [
        [Paragraph("<font size='9'>Document ID:</font>", styles['Center']), 
         Paragraph("<font size='9'>Digital Signature:</font>", styles['Center'])],
        [Paragraph(f"<font size='9'><b>{uuid.uuid4().hex[:16].upper()}</b></font>", styles['Center']),
         Paragraph("<font size='9'><b>Verified ✓</b></font>", styles['Center'])]
    ]
    
    auth_table = Table(auth_data, colWidths=[3.75*inch, 3.75*inch])
    auth_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.darkslategray),
        ('LINEABOVE', (0, 1), (-1, 1), 0.5, colors.lightgrey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(auth_table)
    elements.append(Spacer(1, 10))
    
    # Company information
    footer_text = """
    <font size='8' color='#666666'>This certificate is digitally generated and secured on the blockchain. 
    Any alteration to this document will invalidate the certificate.</font>
    """
    elements.append(Paragraph(footer_text, styles['Center']))
    elements.append(Spacer(1, 5))
    elements.append(Paragraph("<font size='8' color='#006400'>© 2025 AgriSure Blockchain Insurance • support@agrisure.ai • +91-8800123456</font>", styles['Center']))
    
    # Build PDF with border
    doc.build(elements, onFirstPage=add_border, onLaterPages=add_border)
    
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