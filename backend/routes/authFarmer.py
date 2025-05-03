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
def signup():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    
    # Check for both spellings of Aadhaar/Aadhar
    aadhaar_number = data.get("aadhaar_number")
    
    full_name = data.get("full_name")
    phone = data.get("phone")
    upi_id = data.get("upi_id")
    address = data.get("address")
    language_pref = data.get("language_pref")

    if not all([email, password, aadhaar_number, full_name, phone]):
        return jsonify({"error": "Email, password, Aadhaar number, and full name are required"}), 400

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
            phone=phone,
            upi_id=upi_id,
            address=address,
            language_pref=language_pref,
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

@farmer_auth_bp.route("/update-profile", methods=["PUT"])
@token_required
@farmer_required
def update_profile():
    db = next(get_db())
    email = request.user.get("email")

    if not email:
        return jsonify({"error": "Email not found in session"}), 400

    farmer = db.query(Farmer).filter_by(email=email).first()
    if not farmer:
        return jsonify({"error": "Farmer not found"}), 404

    data = request.json
    phone = data.get("phone")
    address = data.get("address")
    upi_id = data.get("upi_id")
    language_pref = data.get("language_pref")
    full_name = data.get("full_name")

    try:
        if phone:
            farmer.phone = phone
        if address:
            farmer.address = address
        if upi_id:
            farmer.upi_id = upi_id
        if language_pref:
            farmer.language_pref = language_pref
        if full_name:
            farmer.full_name = full_name

        db.commit()

        return jsonify({
            "message": "Profile updated successfully",
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

    except Exception as e:
        db.rollback()
        return jsonify({"error": "Profile update failed", "detail": str(e)}), 500
    

@farmer_auth_bp.route("/dashboard", methods=["GET"])
@token_required
@farmer_required
def get_dashboard_date():
    from models import InsPolicy  # Import the InsPolicy model
    from models import Claims  # Import the Claims model
    db = next(get_db())
    email = request.user.get("email")

    if not email:
        return jsonify({"error": "Email not found in session"}), 400

    # Fetch farmer details
    farmer = db.query(Farmer).filter_by(email=email).first()
    if not farmer:
        return jsonify({"error": "Farmer not found"}), 404

    # Fetch active policies
    active_policies = db.query(InsPolicy).filter_by(aadhaar_number=farmer.aadhaar_number, status="active").all()
    active_policies_count = len(active_policies)
    total_premium_amount = sum(policy.premium_amount for policy in active_policies)
    total_amount_insured = sum(policy.coverage_amount for policy in active_policies)

    # Fetch recent transactions (example: premium payments)
    recent_transactions = db.query(Claims).filter_by(aadhaar_number=farmer.aadhaar_number).order_by(Claims.claim_date.desc()).limit(5).all()
    transactions_data = [
        {
            "transactionId": claim.claim_id,
            "type": "Claim Settlement",
            "amount": claim.claim_amt,
            "date": claim.claim_date.isoformat() if claim.claim_date else "N/A",
            "status": claim.claim_sts.value if claim.claim_sts else "N/A"
        }
        for claim in recent_transactions
    ]

    # Example weather alerts (replace with dynamic data if available)
    weather_alerts = [
        {
            "type": "Heavy Rainfall",
            "date": "2025-05-15",
            "location": "Northern Region",
            "impact": "Moderate"
        },
        {
            "type": "Heatwave",
            "date": "2025-05-18",
            "location": "All Regions",
            "impact": "High"
        }
    ]

    # Prepare dashboard data
    dashboard_data = {
        "farmer": {
            "name": farmer.full_name
        },
        "stats": {
            "activePolicies": active_policies_count,
            "totalPremiumAmount": total_premium_amount,
            "totalAmountInsured": total_amount_insured
        },
        "weatherAlerts": weather_alerts,
        "recentTransactions": transactions_data
    }

    return jsonify(dashboard_data), 200
