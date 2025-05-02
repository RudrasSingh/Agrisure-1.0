from flask import Flask
from config import settings
from backend.database import Base, engine
from .models import user, claim #TODO: fix import statement
from .routes import authFarmer

# Create all tables if not exist
Base.metadata.create_all(bind=engine)

app = Flask(__name__)
app.config["DEBUG"] = settings.FLASK_DEBUG

# Register your route blueprints
app.register_blueprint(authFarmer)
if __name__ == "__main__":
    app.run(host=settings.FLASK_HOST, port=settings.FLASK_PORT)
