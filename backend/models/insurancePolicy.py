from sqlalchemy import Column, String, Numeric, Date, TIMESTAMP, ForeignKey, Enum
from database import Base
from sqlalchemy.orm import relationship
import enum
import io
import os
import uuid
import requests
from datetime import datetime
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# You can define Enums here or import from your enums module
class PolicyStatusEnum(enum.Enum):
    draft = 'draft'
    pending = 'pending'
    active = 'active'
    expired = 'expired'
    claimed = 'claimed'
    settled = 'settled'
    cancelled = 'cancelled'
    rejected = 'rejected'

class PolicyTypeEnum(enum.Enum):
    basic = 'basic'
    comprehensive = 'comprehensive'
    weather_indexed = 'weather-indexed'
    input_cost = 'input-cost'
    yield_based = 'yield-based'
    premium_subsidized = 'premium-subsidized'
    group_policy = 'group-policy'
    parametric = 'parametric'

class InsPolicy(Base):
    __tablename__ = "ins_policies"
    __table_args__ = {"schema": "AgriSure"}

    policy_num = Column(String, primary_key=True)
    aadhaar_number = Column(
        String,
        ForeignKey("AgriSure.farmer.aadhaar_number", ondelete="CASCADE"),
        nullable=False
    )
    coverage_amount = Column(Numeric, nullable=False)
    premium_amount = Column(Numeric, nullable=False)
    start_date = Column(Date)
    end_date = Column(Date)
    status = Column(Enum(PolicyStatusEnum), default=PolicyStatusEnum.active)
    policy_type = Column(Enum(PolicyTypeEnum))
    created_at = Column(TIMESTAMP)
    insurer_id = Column(String, ForeignKey("AgriSure.insurer.insurer_id"), nullable=False)
    # Define the relationship to Claims
    claims = relationship("Claims", back_populates="policy")
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

def generate_insurance_pdf(farmer_name, contact, policy_num, contract_address, issue_date, coverage_amount, premium_amount, start_date, end_date, policy_type, insurer_name="AgriSure Insurance"):
    """Generate a detailed insurance certificate PDF"""
    buffer = io.BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,  # Reduced margins for more space
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
        title=f"Insurance Certificate - {policy_num}"
    )
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=1)) 
    styles.add(ParagraphStyle(name='Right', alignment=2))

    # Modify existing styles
    styles['Title'].alignment = 1
    styles['Title'].spaceAfter = 6
    styles['Title'].fontSize = 18
    
    # Add custom styles
    styles.add(ParagraphStyle(name='Heading', fontSize=12, alignment=0, spaceAfter=6, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='SubHeading', fontSize=10, alignment=0, spaceAfter=3, fontName='Helvetica-Bold'))
    
    # Get logo from URL
    logo_url = "https://xrcemypzyjsxoihkckin.supabase.co/storage/v1/object/public/agrisure//Untitled-1.png"
    
    # Try to fetch the logo from URL
    import requests
    from io import BytesIO
    from reportlab.lib.utils import ImageReader
    
    try:
        response = requests.get(logo_url)
        if response.status_code == 200:
            logo_data = BytesIO(response.content)
            logo = Image(logo_data, width=2*inch, height=1.2*inch)
        else:
            # Fallback to local logo if URL fails
            logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'logo.png')
            if os.path.exists(logo_path):
                logo = Image(logo_path, width=2*inch, height=1.2*inch)
            else:
                # No logo available
                logo = None
    except Exception as e:
        print(f"Error loading logo: {str(e)}")
        # Try local logo as fallback
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'logo.png')
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=2*inch, height=1.2*inch)
        else:
            logo = None
    
    # Create a styled header
    header_data = [[]]
    
    # Add logo if available
    if logo:
        header_data[0].append(logo)
    else:
        header_data[0].append(Paragraph("<font size=14>AgriSure</font>", styles['Center']))
    
    # Add titles next to logo
    title_cell = []
    title_cell.append(Paragraph("<font size=18 color='#006400'><b>AGRISURE BLOCKCHAIN</b></font>", styles['Center']))
    title_cell.append(Paragraph("<font size=14 color='#228B22'>Crop Insurance Certificate</font>", styles['Center']))
    title_cell.append(Paragraph(f"<font size=10>Policy Number: {policy_num}</font>", styles['Center']))
    header_data[0].append(title_cell)
    
    # Create header table
    header_table = Table(header_data, colWidths=[2.5*inch, 3*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('ALIGN', (1, 0), (1, 0), 'LEFT'),
    ]))
    elements.append(header_table)
    
    # Add a decorative line
    elements.append(Spacer(1, 0.1*inch))
    from reportlab.platypus import HRFlowable
    elements.append(HRFlowable(width="100%", thickness=1, lineCap='round', 
                            color=colors.green, spaceBefore=1, spaceAfter=1))
    elements.append(Spacer(1, 0.1*inch))
    
    # Add certificate message
    certificate_msg = f"""
    <font size=10>This certificate confirms that <b>{farmer_name}</b> has purchased crop insurance 
    coverage under our AgriSure Blockchain Insurance program. This policy is secured by blockchain 
    technology to ensure transparency and immutability of the insurance contract.</font>
    """
    elements.append(Paragraph(certificate_msg, styles['Center']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Format dates for display
    formatted_start_date = start_date if isinstance(start_date, str) else start_date.strftime("%B %d, %Y")
    formatted_end_date = end_date if isinstance(end_date, str) else end_date.strftime("%B %d, %Y")
    
    # Format currency values
    formatted_coverage = f"₹ {float(coverage_amount):,.2f}"
    formatted_premium = f"₹ {float(premium_amount):,.2f}"
    
    # Policy details section with better styling
    elements.append(Paragraph("<font color='#006400'>POLICY DETAILS</font>", styles['Heading']))
    elements.append(Spacer(1, 0.1*inch))
    
    # Create detailed info table with better styling
    policy_data = [
        ["Farmer Name:", farmer_name, "Policy Number:", policy_num],
        ["Contact:", contact, "Policy Type:", policy_type.replace('_', ' ').title() if isinstance(policy_type, str) else str(policy_type)],
        ["Coverage Amount:", formatted_coverage, "Premium Amount:", formatted_premium],
        ["Start Date:", formatted_start_date, "End Date:", formatted_end_date],
        ["Issued On:", issue_date, "Insurer:", insurer_name],
    ]
    
    # Create styled table
    policy_table = Table(policy_data, colWidths=[1.3*inch, 2*inch, 1.3*inch, 2*inch])
    policy_table.setStyle(TableStyle([
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.lightgreen),
        ('BOX', (0, 0), (-1, -1), 1, colors.darkgreen),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgreen),
        ('BACKGROUND', (2, 0), (2, -1), colors.lightgreen),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.darkgreen),
        ('TEXTCOLOR', (2, 0), (2, -1), colors.darkgreen),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.beige]),
    ]))
    elements.append(policy_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Blockchain verification section with improved styling
    elements.append(Paragraph("<font color='#006400'>BLOCKCHAIN VERIFICATION</font>", styles['Heading']))
    elements.append(Spacer(1, 0.1*inch))
    
    blockchain_data = [
        ["Contract Address:", contract_address],
        ["Verification Status:", "Verified on Blockchain ✓"],
        ["Timestamp:", datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")]
    ]
    
    blockchain_table = Table(blockchain_data, colWidths=[1.8*inch, 4.8*inch])
    blockchain_table.setStyle(TableStyle([
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.darkgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.darkblue),
    ]))
    elements.append(blockchain_table)
    
    # Terms and conditions section with better formatting
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph("<font color='#006400'>TERMS & CONDITIONS</font>", styles['Heading']))
    elements.append(Spacer(1, 0.1*inch))
    
    terms_text = """
    <font size=9><b>1.</b> This policy is subject to the terms and conditions mentioned in the policy document.
    <b>2.</b> Claims must be filed within 30 days of the loss incident.
    <b>3.</b> The policy is valid only for the duration mentioned above.
    <b>4.</b> Policy verification can be done by scanning the QR code or using the contract address on AgriSure portal.
    <b>5.</b> Premium amount is non-refundable except as per the cancellation policy.</font>
    """
    elements.append(Paragraph(terms_text, styles['Normal']))
    
    # Footer with improved design
    elements.append(Spacer(1, 0.3*inch))
    elements.append(HRFlowable(width="100%", thickness=1, lineCap='round', 
                            color=colors.green, spaceBefore=1, spaceAfter=1))
    elements.append(Spacer(1, 0.1*inch))
    
    footer_text = """
    <font size=8 color='#006400'>This certificate is digitally generated and secured by blockchain technology.
    Any alteration to this document will invalidate the certificate.</font>
    """
    elements.append(Paragraph(footer_text, styles['Center']))
    
    elements.append(Paragraph(f"<font size=8>Document ID: {uuid.uuid4().hex[:16].upper()}</font>", styles['Center']))
    elements.append(Paragraph("<font size=8>© AgriSure Blockchain Insurance • support@agrisure.ai • +91-8800123456</font>", styles['Center']))
    
    # Build PDF
    doc.build(elements)
    
    # Return PDF bytes
    buffer.seek(0)
    return buffer.getvalue()