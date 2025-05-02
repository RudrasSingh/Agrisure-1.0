# create_tables.py
from database import Base, engine
from models.farmer import Farmer
from models.blockData import BlockchainIn
from models.claim import Claims
from models.insurancePolicy import InsPolicy
from models.insurer import Insurer
from models.lands import LandData


Base.metadata.create_all(bind=engine)
print("✅ Tables created!")
