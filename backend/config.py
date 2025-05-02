import os
from dotenv import load_dotenv

load_dotenv()

class Settings:  

    # Supabase (Postgres + Auth)
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    

    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")

    SQLALCHEMY_DATABASE_URL = (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
    )
    # Sentinel Hub
    SH_CLIENT_ID = os.getenv("SH_CLIENT_ID")
    SH_CLIENT_SECRET = os.getenv("SH_CLIENT_SECRET")
    SH_BASE_URL = os.getenv("SH_BASE_URL", "https://services.sentinel-hub.com")

    # # Mailjet
    # MAILJET_API_KEY = os.getenv("MAILJET_API_KEY")
    # MAILJET_SECRET = os.getenv("MAILJET_SECRET")

    # SMS (e.g. Twilio trial)
    # SMS_ACCOUNT_SID = os.getenv("SMS_ACCOUNT_SID")
    # SMS_AUTH_TOKEN = os.getenv("SMS_AUTH_TOKEN")
    # SMS_FROM_NUMBER = os.getenv("SMS_FROM_NUMBER")

    # # Web3 / Blockchain
    # WEB3_PROVIDER_URI = os.getenv("WEB3_PROVIDER_URI")
    # CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
    # CONTRACT_ABI_PATH = os.getenv("CONTRACT_ABI_PATH")  # local path to ABI JSON

settings = Settings()
