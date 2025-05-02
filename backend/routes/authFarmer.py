from flask import Blueprint, request, jsonify, make_response
from database import supabase, SessionLocal
from models.farmer import Farmer
from datetime import datetime
from utils.auth import token_required, farmer_required
from sqlalchemy.orm import Session
from werkzeug.utils import secure_filename
import os

farmer_auth_bp = Blueprint("farmer_auth", __name__, url_prefix="/api/v1/farmer")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@farmer_auth_bp.route("/signup", methods=["POST"])
def signup():
     # Use request.form for text data, request.files for files
    email = request.form.get("email")
    password = request.form.get("password")
    aadhaar_number = request.form.get("aadhaar_number")
    full_name = request.form.get("full_name")
    phone = request.form.get("phone")

    pdf_file = request.files.get("landDocument") 

    if not all([email, password, aadhaar_number, full_name, phone, pdf_file]):
        return jsonify({"error": "All fields including Aadhaar PDF are required"}), 400

    if pdf_file and pdf_file.filename.endswith('.pdf'):
        filename = secure_filename(pdf_file.filename)
        filepath = os.path.join("./backend/uploads", filename)  # Create this folder if not exists
        pdf_file.save(filepath)
    else:
        return jsonify({"error": "Invalid file format. Please upload a PDF"}), 400

    try:
        db = next(get_db())

        if db.query(Farmer).filter((Farmer.email == email) | (Farmer.aadhaar_number == aadhaar_number)).first():
            return jsonify({"error": "Email or Aadhaar number already registered"}), 400

        # Supabase signup
        supabase_response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })

        if not supabase_response or not supabase_response.user:
            return jsonify({"error": "Supabase signup failed"}), 500

        new_farmer = Farmer(
            email=email,
            aadhaar_number=aadhaar_number,
            full_name=full_name,
            created_at=datetime.now(),
            phone=phone
        )
        db.add(new_farmer)
        db.commit()

        return jsonify({
            "message": "Farmer account created successfully",
            "user": {
                "email": email,
                "role": "farmer"
            }
        }), 201

    except Exception as e:
        return jsonify({"error": "Signup failed", "detail": str(e)}), 500


@farmer_auth_bp.route("/login", methods=["POST"])
def login():
    db = next(get_db())

    token = request.cookies.get("access_token")
    if token:
        try:
            user_info = supabase.auth.get_user(token)
            email = user_info.user.email
            farmer = db.query(Farmer).filter_by(email=email).first()
            if farmer:
                return jsonify({
                    "message": "Already logged in",
                    "user": {
                        "email": email,
                        "role": "farmer",
                        "full_name": farmer.full_name
                    }
                }), 200
        except Exception:
            pass  # Invalid token

    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not all([email, password]):
        return jsonify({"error": "Email and password required"}), 400

    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if not response.user or not response.session:
            return jsonify({"error": "Invalid credentials"}), 401

        farmer = db.query(Farmer).filter_by(email=email).first()
        if not farmer:
            return jsonify({"error": "Farmer not found in database"}), 404

        res = make_response(jsonify({
            "message": "Login successful",
            "user": {
                "email": email,
                "role": "farmer",
                "full_name": farmer.full_name
            }
        }))
        res.set_cookie(
            key="access_token",
            value=response.session.access_token,
            httponly=True,
            secure=True,  # True in prod
            samesite="None",
            max_age=3600
        )

        return res

    except Exception as e:
        return jsonify({"error": "Login failed", "detail": str(e)}), 500


@farmer_auth_bp.route("/logout", methods=["POST"])
@token_required
def logout():
    response = make_response(jsonify({"message": "Logged out successfully"}))
    response.set_cookie("access_token", "", expires=0)
    return response


@farmer_auth_bp.route("/profile", methods=["GET"])
@token_required
@farmer_required
def get_current_farmer():
    db = next(get_db())
    email = request.user.get("email")

    if not email:
        return jsonify({"error": "Email not found in session"}), 400

    farmer = db.query(Farmer).filter_by(email=email).first()
    if not farmer:
        return jsonify({"error": "Farmer not found"}), 404

    return jsonify({
        "message": "Profile fetched successfully",
        "profile": {
            "aadhaar_number": "XXXX-XXXX-" + farmer.aadhaar_number[-4:],
            "phone" : farmer.phone,
            "full_name": farmer.full_name,
            "email": farmer.email,
            "address": farmer.address,
            "upi_id": farmer.upi_id,
            "land_doc_url": farmer.land_doc_url,
            "kyc_verified": farmer.kyc_verified,
            "language_pref": farmer.language_pref,
            "wallet_address": farmer.wallet_address,
            "created_at": farmer.created_at.isoformat() if farmer.created_at else None,

        }
    }), 200
