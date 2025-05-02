from sqlalchemy import Column, String, Text, Boolean, Numeric, TIMESTAMP, ForeignKey
from database import Base

class BlockchainIn(Base):
    __tablename__ = "blockchain_in"
    __table_args__ = {"schema": "AgriSure"}

    aadhaar_number = Column(
        String,
        ForeignKey("AgriSure.farmer.aadhaar_number", ondelete="CASCADE"),
        primary_key=True
    )
    Address = Column(Text)
    crop_name = Column(Text, nullable=False)
    sum_insured = Column(Text, nullable=False)
    premium_paid = Column(Numeric, nullable=False)
    is_insured = Column(Boolean, nullable=False)
    insurance_date = Column(TIMESTAMP, nullable=False)
    trans_hash = Column(Text, unique=True, nullable=False)
    contract_add = Column(Text, nullable=False)
    claim_sts = Column(Text, nullable=False)
    policy_num = Column(
        String,
        ForeignKey("ins_policies.policy_num", ondelete="CASCADE")
    )
    insurer_id = Column(String, ForeignKey("insurer.insurer_id"), nullable=False)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}