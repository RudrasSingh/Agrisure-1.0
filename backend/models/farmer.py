from sqlalchemy import Column, String, Text, Boolean, TIMESTAMP
from database import Base

class Farmer(Base):
    __tablename__ = "farmer"
    __table_args__ = {"schema": "AgriSure"}

    aadhaar_number = Column(String, primary_key=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    address = Column(Text)
    upi_id = Column(String)
    land_doc_url = Column(String)
    kyc_verified = Column(Boolean, default=False)
    language_pref = Column(String)
    wallet_address = Column(String)
    created_at = Column(TIMESTAMP)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}