from flask import Flask,jsonify
from models import *  # Import all models to register them with SQLAlchemy
from routes.authFarmer import farmer_auth_bp
from routes.insurance import insurance_bp
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    # CORS(app,
    #      supports_credentials=True,
    #      origins=["*"])  # Adjust the origins as needed

    @app.route("/health", methods=["GET"]) 
    def health_check():
        return jsonify({"status": "healthy"})

    # Register all blueprints
    app.register_blueprint(farmer_auth_bp)
    app.register_blueprint(insurance_bp)
    # Add other blueprints here as needed

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)