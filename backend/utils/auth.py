from functools import wraps
from flask import request, jsonify
from database import supabase, SessionLocal
from models.farmer import Farmer
from models.insurer import Insurer

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get("access_token")
        if not token:
            return jsonify({"error": "Session token missing"}), 401

        try:
            user = supabase.auth.get_user(token).user
            if not user:
                return jsonify({"error": "Invalid session"}), 401

            email = user.email
            db = SessionLocal()

            # Check if user is a Farmer
            farmer = db.query(Farmer).filter_by(email=email).first()
            if farmer:
                request.user = {
                    "role": "farmer",
                    "email": email
                }
                db.close()
                return f(*args, **kwargs)

            # Check if user is an Insurer
            insurer = db.query(Insurer).filter_by(email=email).first()
            if insurer:
                request.user = {
                    "role": "insurer",
                    "email": email
                }
                db.close()
                return f(*args, **kwargs)

            db.close()
            return jsonify({"error": "User not registered"}), 404

        except Exception as e:
            return jsonify({"error": "Token error", "detail": str(e)}), 401

    return decorated

def insurer_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(request, "user") or request.user.get("role") != "insurer":
            return jsonify({"error": "Forbidden: Insurer access only"}), 403
        return f(*args, **kwargs)
    return decorated

def farmer_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(request, "user") or request.user.get("role") != "farmer":
            return jsonify({"error": "Forbidden: Farmer access only"}), 403
        return f(*args, **kwargs)
    return decorated
