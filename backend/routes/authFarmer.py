from flask import Blueprint, request, jsonify, make_response
from database import supabase, SessionLocal
from models.farmer import Farmer
from datetime import datetime
from utils.auth import token_required, farmer_required
from sqlalchemy.orm import Session
farmer_auth_bp = Blueprint("farmer_auth", __name__, url_prefix="/api/v1/farmer")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@farmer_auth_bp.route("/signup", methods=["POST"])
def send_otp():
    data = request.json
    phone = data.get("phone")
    aadhaar = data.get("aadhaar")  # Now requiring Aadhaar during signup

    if not phone or not aadhaar:
        return jsonify({"error": "Phone number and Aadhaar number are required"}), 400

    try:
        # Check if the Aadhaar is already registered
        db = next(get_db())
        existing_farmer = db.query(Farmer).filter_by(aadhaar=aadhaar).first()
        if existing_farmer:
            return jsonify({"error": "This Aadhaar number is already registered"}), 400

        # Send OTP to the phone number
        supabase.auth.sign_in_with_otp({"phone": phone})
        
        # IMPORTANT: Don't include Aadhaar in the response
        return jsonify({"message": "OTP sent to phone"}), 200

    except Exception as e:
        return jsonify({"error": "OTP request failed", "detail": str(e)}), 500


@farmer_auth_bp.route("/verify-otp", methods=["POST"])
def verify_otp():
    data = request.json
    phone = data.get("phone")
    otp = data.get("otp")
    aadhaar = data.get("aadhaar")
    name = data.get("name", "")

    if not all([phone, otp, aadhaar]):
        return jsonify({"error": "Phone, OTP, and Aadhaar number are required"}), 400

    try:
        result = supabase.auth.verify_otp({
            "phone": phone,
            "token": otp,
            "type": "sms"
        })

        user = result.user
        session = result.session
        
        if not user or not session:
            return jsonify({"error": "OTP verification failed"}), 400

        db = next(get_db())

        # Check if already exists
        if db.query(Farmer).filter_by(aadhaar=aadhaar).first():
            return jsonify({"error": "Farmer already registered with this Aadhaar"}), 400

        new_farmer = Farmer(
            farmer_id=user.id,
            phone=phone,
            aadhaar=aadhaar,
            name=name,
            created_at=datetime.utcnow()
        )
        db.add(new_farmer)
        db.commit()

        res = make_response(jsonify({
            "message": "Farmer account verified and saved",
            "user_id": user.id,
            "name": name,
            "phone": phone
        }))
        
        # Set access token in cookie
        res.set_cookie(
            key="access_token",
            value=session.access_token,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="None",
            max_age=3600
        )
        # Set access token in cookie for production
        # res.set_cookie(
        #     key="access_token",
        #     value=session.access_token,
        #     httponly=True,
        #     secure=True,  # FIXME: Set to True in production with HTTPS
        #     samesite="None",
        #     max_age=3600
        # )

        return res, 201

    except Exception as e:
        return jsonify({"error": "Verification failed", "detail": str(e)}), 500


@farmer_auth_bp.route("/login", methods=["POST"])
def login_request_otp():
    """Request OTP for login"""
    data = request.json
    phone = data.get("phone")
    
    if not phone:
        return jsonify({"error": "Phone number is required"}), 400
        
    try:
        # Check if the user exists
        db = next(get_db())
        existing_farmer = db.query(Farmer).filter_by(phone=phone).first()
        
        if not existing_farmer:
            return jsonify({"error": "No account found with this phone number"}), 404
            
        # Send OTP
        supabase.auth.sign_in_with_otp({"phone": phone})
        
        # IMPORTANT: Don't include Aadhaar in the response
        return jsonify({
            "message": "OTP sent to phone",
            "name": existing_farmer.name
        }), 200
        
    except Exception as e:
        return jsonify({"error": "Login OTP request failed", "detail": str(e)}), 500


@farmer_auth_bp.route("/login/verify", methods=["POST"])
def login_verify_otp():
    """Verify OTP for login"""
    data = request.json
    phone = data.get("phone")
    otp = data.get("otp")
    
    if not phone or not otp:
        return jsonify({"error": "Phone number and OTP are required"}), 400
        
    try:
        result = supabase.auth.verify_otp({
            "phone": phone,
            "token": otp,
            "type": "sms"
        })
        
        user = result.user
        session = result.session
        
        if not user or not session:
            return jsonify({"error": "OTP verification failed"}), 400
            
        # Get farmer details
        db = next(get_db())
        farmer = db.query(Farmer).filter_by(phone=phone).first()
        
        if not farmer:
            return jsonify({"error": "Farmer not found"}), 404
            
        res = make_response(jsonify({
            "message": "Login successful",
            "user_id": user.id,
            "farmer_details": {
                "name": farmer.name,
                "phone": farmer.phone
                # IMPORTANT: Aadhaar removed from response
            }
        }))
        
        # Set access token in cookie
        res.set_cookie(
            key="access_token",
            value=session.access_token,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="None",
            max_age=3600
        )
        
        return res, 200
        
    except Exception as e:
        return jsonify({"error": "Login verification failed", "detail": str(e)}), 500


@farmer_auth_bp.route("/logout", methods=["POST"])
def logout():
    """Logout the farmer by clearing cookies"""
    response = make_response(jsonify({"message": "Logged out successfully"}))
    response.set_cookie("access_token", "", expires=0)  # Clear the cookie
    return response


@farmer_auth_bp.route("/me", methods=["GET"])
@token_required
@farmer_required
def get_current_farmer():
    """Get the current logged-in farmer details"""
    # Farmer is already authenticated and loaded by the middleware
    farmer = request.farmer
    
    # Return all fields from the farmer model except Aadhaar
    return jsonify({
        "farmer": {
            "aadhaar_number": "XXXX-XXXX-" + farmer.aadhaar_number[-4:] if farmer.aadhaar_number else None,
            "full_name": farmer.full_name,
            "phone": farmer.phone,
            "address": farmer.Address,
            "upi_id": farmer.upi_id,
            "land_doc_url": farmer.land_doc_url,
            "kyc_verified": farmer.kyc_verified,
            "language_pref": farmer.language_pref,
            "wallet_address": farmer.wallet_address,
            "created_at": farmer.created_at.isoformat() if farmer.created_at else None
        }
    }), 200