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
            user_response = supabase.auth.get_user(token)
            user = user_response.user if user_response else None

            if not user or not user.email:
                return jsonify({"error": "Invalid session"}), 401

            # Hacky but works — attach email to request object
            setattr(request, "user", {"email": user.email})
            return f(*args, **kwargs)

        except Exception as e:
            return jsonify({"error": "Token error", "detail": str(e)}), 401

    return decorated

def farmer_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(request, "user") or "email" not in request.user:
            return jsonify({"error": "Unauthorized access"}), 401

        email = request.user["email"]
        db = SessionLocal()
        try:
            farmer = db.query(Farmer).filter_by(email=email).first()
            if not farmer:
                return jsonify({"error": "Forbidden: Farmer access only"}), 403

            request.user["role"] = "farmer"
            request.user["farmer"] = farmer
            return f(*args, **kwargs)
        finally:
            db.close()
    return decorated

def insurer_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(request, "user") or "email" not in request.user:
            return jsonify({"error": "Unauthorized access"}), 401

        email = request.user["email"]
        db = SessionLocal()
        try:
            insurer = db.query(Insurer).filter_by(email=email).first()
            if not insurer:
                return jsonify({"error": "Forbidden: Insurer access only"}), 403

            request.user["role"] = "insurer"
            request.user["insurer"] = insurer
            return f(*args, **kwargs)
        finally:
            db.close()
    return decorated
