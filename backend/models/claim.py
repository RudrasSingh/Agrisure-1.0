from sqlalchemy import Column, String, Text, Numeric, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Claims(Base):
    _tablename_ = "claims"
    _table_args_ = {"schema": "AgriSure"}

    # Columns for Claims
    claim_id = Column(String, primary_key=True, nullable=False)
    policy_num = Column(String, ForeignKey("AgriSure.ins_policies.policy_num", ondelete="CASCADE"), nullable=False)
    aadhaar_number = Column(String, ForeignKey("AgriSure.farmer.aadhaar_number", ondelete="CASCADE"), nullable=False)
    claim_amt = Column(Numeric, nullable=False)
    claim_sts = Column("policy_status_enum", "AgriSure".policy_status_enum, default="pending")  # Reference to Enum
    claim_date = Column(TIMESTAMP, default="now()")  # When the claim was filed
    settlement_date = Column(TIMESTAMP, nullable=True)  # The date when the claim is settled (null if not settled yet)
    descr = Column(Text, nullable=True)  # Claim description - Contains the url for the AI doc processed for the claim 
    confidence_score = Column(Numeric, nullable=False)  # contains the confidence score of the AI model fromm satellite
    reason_ = Column(Text, nullable=True)  # Reason for claim (optional)
    created_at = Column(TIMESTAMP, default="now()")  # When the record is created
    updated_at = Column(TIMESTAMP, nullable=True)  # When the record is updated (nullable)

    # Relationships
    policy = relationship("InsPolicies", back_populates="claims")  # Relating with ins_policies table
    farmer = relationship("Farmer", back_populates="claims")  # Relating with farmer table

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self._table_.columns}