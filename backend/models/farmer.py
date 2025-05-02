from sqlalchemy import Column, String, Text, Boolean, TIMESTAMP
from database import Base

class Farmer(Base):
    _tablename_ = "farmer"
    _table_args_ = {"schema": "AgriSure"}

    aadhaar_number = Column(String, primary_key=True, nullable=False)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    Address = Column(Text)
    upi_id = Column(String)
    land_doc_url = Column(String)
    kyc_verified = Column(Boolean, default=False)
    language_pref = Column(String)
    wallet_address = Column(String)
    created_at = Column(TIMESTAMP)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self._table_.columns}