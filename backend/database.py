from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from config import settings
from supabase import create_client

DATABASE_URL = settings.SQLALCHEMY_DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

