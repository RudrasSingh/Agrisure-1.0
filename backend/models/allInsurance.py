from sqlalchemy import Column, String, Numeric, Date, TIMESTAMP, ForeignKey, Enum
from database import Base
from sqlalchemy.orm import relationship
import enum

class AvailableInsurance(Base):
    __tablename__ = "available_insurances"
    __table_args__ = {"schema": "AgriSure"}

    insurance_id = Column(String, primary_key=True)  # Unique ID for the insurance
    insurer_id = Column(String, ForeignKey("AgriSure.insurer.insurer_id", ondelete="CASCADE"), nullable=False)
    policy_name = Column(String, nullable=False)  # Name of the insurance policy
    policy_type = Column(Enum(PolicyTypeEnum), nullable=False)  # Type of the policy
    coverage_amount = Column(Numeric, nullable=False)  # Maximum coverage amount
    premium_amount = Column(Numeric, nullable=False)  # Premium amount
    description = Column(String, nullable=True)  # Description of the policy
    start_date = Column(Date, nullable=False)  # Start date of the policy availability
    end_date = Column(Date, nullable=False)  # End date of the policy availability
    created_at = Column(TIMESTAMP, default="now()")  # Record creation timestamp
    updated_at = Column(TIMESTAMP, nullable=True)  # Record update timestamp

    # Relationship to Insurer
    insurer = relationship("Insurer", back_populates="available_insurances")

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}