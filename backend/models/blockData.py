from sqlalchemy import Column, String, Text, Boolean, Numeric, TIMESTAMP, ForeignKey
from database import Base

class BlockchainIn(Base):
    _tablename_ = "blockchain_in"
    _table_args_ = {"schema": "AgriSure"}

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
        ForeignKey("AgriSure.ins_policies.policy_num", ondelete="CASCADE")
    )

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self._table_.columns}