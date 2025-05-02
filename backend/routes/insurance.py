from flask import Blueprint, request, jsonify
from database import SessionLocal
from models.insurancePolicy import InsPolicy
from models.farmer import Farmer
from datetime import datetime
from utils.auth import token_required, farmer_required
from sqlalchemy.exc import IntegrityError

insurance_bp = Blueprint("farmer_insurance_bp", __name__, url_prefix="/api/v1/insurance")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@insurance_bp.route("/buy-policy", methods=["POST"])
@token_required
@farmer_required
def buy_policy():
    db = next(get_db())

    email = request.user.get("email")
    if not email:
        return jsonify({"error": "Email not found in session"}), 403

    farmer = db.query(Farmer).filter_by(email=email).first()
    if not farmer or not farmer.aadhaar_number:
        return jsonify({"error": "Farmer not found or Aadhaar missing"}), 404

    aadhaar_number = farmer.aadhaar_number

    data = request.json
    policy_num = data.get("policy_num")
    coverage_amount = data.get("coverage_amount")
    premium_amount = data.get("premium_amount")
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    insurer_id = data.get("insurer_id")
    policy_type = data.get("policy_type", "basic")

    if not all([policy_num, coverage_amount, premium_amount, start_date, end_date, insurer_id]):
        return jsonify({"error": "Missing one or more required fields"}), 400

    try:
        coverage_amount = float(coverage_amount)
        premium_amount = float(premium_amount)
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")

        new_policy = InsPolicy(
            policy_num=policy_num,
            aadhaar_number=aadhaar_number,
            coverage_amount=coverage_amount,
            premium_amount=premium_amount,
            start_date=start_date,
            end_date=end_date,
            status="active",
            policy_type=policy_type,
            created_at=datetime.now(),
            insurer_id=insurer_id
        )

        db.add(new_policy)
        db.commit()

        return jsonify({
            "message": "Insurance policy purchased successfully",
            "policy_num": new_policy.policy_num,
            "status": new_policy.status.value
        }), 201

    except Exception as e:
        db.rollback()
        return jsonify({"error": "Policy purchase failed", "detail": str(e)}), 500
