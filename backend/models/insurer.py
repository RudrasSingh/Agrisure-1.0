from sqlalchemy import Column, String, Text, Numeric, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


# Insurer Table Model
class Insurer(Base):
    _tablename_ = "insurer"
    _table_args_ = {"schema": "AgriSure"}

    # Columns for Insurer
    insurer_id = Column(String, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    phone = Column(String, nullable=True)
    organization = Column(String, nullable=True)
    insurance_license = Column(String, nullable=True)

    # Relationships (if any) and methods can be added here

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self._table_.columns}