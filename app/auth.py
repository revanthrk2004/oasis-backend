from flask import Blueprint, request, jsonify, send_file
from .models import User, Booking, db
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, decode_token
from sqlalchemy.exc import IntegrityError
from datetime import timedelta
import uuid
import qrcode
import io

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    required_fields = ["username", "email", "password", "first_name", "last_name", "phone", "address"]
    if not data or not all(k in data for k in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    oasis_card_id = str(uuid.uuid4()).replace("-", "")[:12]
    user = User(
        username=data["username"],
        email=data["email"],
        role="user",
        oasis_card_id=oasis_card_id,
        first_name=data["first_name"],
        last_name=data["last_name"],
        phone=data["phone"],
        address=data["address"]
    )
    user.set_password(data["password"])

    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Username or email already exists"}), 409

    return jsonify({"message": "User registered successfully"}), 201

@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not all(k in data for k in ("username", "password")):
        return jsonify({"error": "Missing username or password"}), 400

    user = User.query.filter_by(username=data["username"]).first()
    if user and user.check_password(data["password"]):
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={"role": user.role},
            expires_delta=timedelta(days=365)
        )
        return jsonify(access_token=access_token), 200

    return jsonify({"error": "Invalid credentials"}), 401

@auth.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    bookings = [{
        "id": b.id,
        "date": b.booking_time.strftime("%Y-%m-%d"),
        "time": b.booking_time.strftime("%H:%M"),
        "guests": b.guest_count,
        "table": b.table_number,
        "notes": b.note
    } for b in user.bookings]

    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "oasis_card_id": user.oasis_card_id,
        "wallet_balance": user.wallet_balance,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone": user.phone,
        "address": user.address,
        "bookings": bookings
    }), 200

@auth.route('/profile', methods=['PATCH'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    updated = False

    if "username" in data:
        if User.query.filter_by(username=data["username"]).first() and user.username != data["username"]:
            return jsonify({"error": "Username already taken"}), 409
        user.username = data["username"]
        updated = True

    if "email" in data:
        if User.query.filter_by(email=data["email"]).first() and user.email != data["email"]:
            return jsonify({"error": "Email already taken"}), 409
        user.email = data["email"]
        updated = True

    if "oasis_card_id" in data:
        if User.query.filter_by(oasis_card_id=data["oasis_card_id"]).first() and user.oasis_card_id != data["oasis_card_id"]:
            return jsonify({"error": "Oasis Card ID already in use"}), 409
        user.oasis_card_id = data["oasis_card_id"]
        updated = True

    # 🔁 New editable fields
    for field in ["first_name", "last_name", "phone", "address"]:
        if field in data:
            setattr(user, field, data[field])
            updated = True

    if updated:
        db.session.commit()
        return jsonify({"message": "Profile updated successfully"}), 200
    else:
        return jsonify({"message": "No changes made"}), 200

@auth.route('/user/oasis-card/qr', methods=['GET'])
def generate_qr_code():
    token = request.args.get('token')
    if not token:
        return jsonify({"error": "Missing token"}), 400

    try:
        decoded = decode_token(token)
        user_id = decoded.get("sub")
    except Exception:
        return jsonify({"error": "Invalid token"}), 401

    user = User.query.get(user_id)
    if not user or not user.oasis_card_id:
        return jsonify({"error": "Oasis Card ID not set"}), 400

    qr_img = qrcode.make(user.oasis_card_id)
    buf = io.BytesIO()
    qr_img.save(buf, format='PNG')
    buf.seek(0)

    return send_file(buf, mimetype='image/png')

@auth.route('/admin/promote', methods=['POST'])
@jwt_required()
def promote_user():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if not current_user or current_user.role != 'admin':
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json()
    username = data.get("username")
    if not username:
        return jsonify({"error": "Username is required"}), 400

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.role = 'admin'
    db.session.commit()
    return jsonify({"message": f"{username} has been promoted to admin"}), 200


@auth.route('/user/oasis-card/pass', methods=['GET'])
@jwt_required()
def download_pkpass():
    try:
        return send_file(
            "pass_generator/OasisCard.pkpass",
            mimetype='application/vnd.apple.pkpass',
            as_attachment=True,
            download_name="OasisCard.pkpass"
        )
    except FileNotFoundError:
        return jsonify({"error": "Pass file not found"}), 404
