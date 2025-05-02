from sqlalchemy import Column, String, Numeric, Date, TIMESTAMP, ForeignKey, Enum
from database import Base
import enum

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
    _tablename_ = "ins_policies"
    _table_args_ = {"schema": "AgriSure"}

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

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self._table_.columns}