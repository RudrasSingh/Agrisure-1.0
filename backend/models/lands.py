from sqlalchemy import Column, String, Float, Text, Date, ForeignKey, JSON
from database import Base

class LandData(Base):
    __tablename__ = "land_data"
    __table_args__ = {"schema": "AgriSure"}

    aadhaar_number = Column(
        String,
        ForeignKey("AgriSure.farmer.aadhaar_number", ondelete="CASCADE"),
        primary_key=True
    )
    coordinates = Column(JSON)
    area_hec = Column(Float)
    crop_type = Column(Text)
    sowing_date = Column(Date)
    exp_yield = Column(Float)
    soil_type = Column(Text)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}