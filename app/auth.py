from flask import Blueprint, request, jsonify, send_file, render_template
from .models import User, Booking, db
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, decode_token
from sqlalchemy.exc import IntegrityError
from datetime import timedelta
import uuid
import qrcode
import io
import os
import json
from openai import OpenAI
from .email_utils import send_email
from itsdangerous import URLSafeTimedSerializer
from flask import url_for
from urllib.parse import quote_plus
from .models import Coupon
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
from .models import VoucherRegistration
from .email_utils import send_email  # Ensure it supports attachments



serializer = URLSafeTimedSerializer(os.environ.get("SECRET_KEY"))
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
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


@auth.route('/forgot-username', methods=['POST'])
def forgot_username():
    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({"error": "Email is required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "No account found with this email"}), 404

    subject = "Your Oasis Bar Username"
    content = f"Hello {user.first_name},\n\nYour username is: {user.username}\n\nCheers,\nOasis Bar Team"
    
    if send_email(user.email, subject, content):
        return jsonify({"message": "Username sent to your email"}), 200
    else:
        return jsonify({"error": "Failed to send email"}), 500



@auth.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({"error": "Email is required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "No account found with this email"}), 404

    token = serializer.dumps(user.email, salt="password-reset-salt")
    encoded_token = quote_plus(token)  # ✅ Encode the token safely
    reset_url = f"https://lighthearted-puppy-bd0fb7.netlify.app/reset-password/{token}"

    subject = "Password Reset for Oasis Bar"
    content = f"Hello {user.first_name},\n\nUse the following link to reset your password:\n{reset_url}\n\nLink expires in 30 minutes."

    if send_email(user.email, subject, content):
        return jsonify({"message": "Password reset link sent to your email"}), 200
    else:
        return jsonify({"error": "Failed to send email"}), 500



@auth.route('/redeem-coupon', methods=['POST'])
@jwt_required()
def redeem_coupon():
    user_id = get_jwt_identity()
    data = request.get_json()
    scanned_text = data.get("code")

    if not scanned_text:
        return jsonify({"error": "No coupon code found"}), 400

    code = scanned_text.strip()
    reg = VoucherRegistration.query.filter_by(voucher_id=code).first()

    if not reg:
        return jsonify({"error": "Invalid or unregistered voucher code"}), 404
    if reg.is_used:
        return jsonify({"error": "This voucher has already been redeemed"}), 409

    # Mark as used
    reg.is_used = True
    reg.used_at = datetime.utcnow()

    # Duplicate into Coupon
    coupon = Coupon(
        code=code,
        redeemed_by=user_id,
        scanned_at=datetime.utcnow(),
        first_name=reg.first_name,
        middle_name=reg.middle_name,
        last_name=reg.last_name,
        email=reg.email,
        phone=reg.phone,
        dob=reg.dob,
        house_number=reg.house_number,
        street=reg.street,
        city=reg.city,
        county=reg.county,
        postcode=reg.postcode,
        country=reg.country,
        raw_data=json.dumps(data)
    )

    db.session.add(coupon)
    db.session.commit()

    return jsonify({"message": "Voucher redeemed successfully"}), 200


@auth.route('/chatbot', methods=['POST'])
@jwt_required(optional=True)
def ai_chatbot():
    data = request.get_json()
    user_message = data.get("message")
    user_id = get_jwt_identity()

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    try:
        # ✅ Load structured data
        file_path = os.path.join(os.path.dirname(__file__), "oasis_info.json")
        with open(file_path, "r") as file:
            oasis_info = json.load(file)

        prompt = (
            "You are an AI assistant for Oasis Bar & Terrace in Canary Wharf, London. "
            "Use only the following data to answer questions accurately and clearly:\n\n"
            f"{json.dumps(oasis_info, indent=2)}\n\n"
            f"User message: {user_message}\n"
            "Only answer based on the above data. Do not make up information."
        )

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an accurate and helpful assistant using structured info only."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.5,
        )

        reply = response.choices[0].message.content

        # ✅ Log to DB
        from .models import ChatLog  # make sure you import this
        log = ChatLog(
            user_id=user_id if user_id else None,
            question=user_message,
            answer=reply,
            flagged="I don't know" in reply
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({"reply": reply})

    except Exception as e:
        print("AI error:", e)
        return jsonify({"error": "AI service failed"}), 500


@auth.route('/chatlogs', methods=['GET'])
@jwt_required()
def get_chat_logs():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if not current_user or current_user.role != 'admin':
        return jsonify({"error": "Admin access required"}), 403

    from .models import ChatLog  # ensure ChatLog is imported

    logs = ChatLog.query.order_by(ChatLog.timestamp.desc()).limit(100).all()

    return jsonify([{
        "id": log.id,
        "user_id": log.user_id,
        "question": log.question,
        "answer": log.answer,
        "flagged": log.flagged,
        "timestamp": log.timestamp.isoformat()
    } for log in logs]), 200



@auth.route('/madri/register', methods=['POST'])
def register_for_madri():
    data = request.get_json()
    required_fields = [
        "first_name", "last_name", "email", "phone", "dob",
        "house_number", "street", "city", "county", "postcode", "country", "consent_given"
    ]

    if not data or not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    if not data.get("consent_given"):
        return jsonify({"error": "Consent is required"}), 400

    # Check if already registered with this email or phone
    existing = VoucherRegistration.query.filter(
        (VoucherRegistration.email == data["email"]) |
        (VoucherRegistration.phone == data["phone"])
    ).first()
    if existing:
        return jsonify({"error": "You have already registered for this voucher"}), 409

    # Save to DB
    reg = VoucherRegistration(
        first_name=data["first_name"],
        middle_name=data.get("middle_name"),
        last_name=data["last_name"],
        email=data["email"],
        phone=data["phone"],
        dob=datetime.strptime(data["dob"], "%Y-%m-%d"),
        house_number=data["house_number"],
        street=data["street"],
        city=data["city"],
        county=data["county"],
        postcode=data["postcode"],
        country=data["country"],
        consent_given=data["consent_given"]
    )
    db.session.add(reg)
    db.session.commit()

    # Generate QR code with only voucher_id
    qr_img = qrcode.make(reg.voucher_id)
    buf = io.BytesIO()
    qr_img.save(buf, format='PNG')
    buf.seek(0)

    # Send QR code to user via email
    subject = "Your Free Madri Pint Voucher 🍺"
    content = f"""
    Hi {reg.first_name},

    Thank you for registering! Attached is your QR code voucher for a free Madri pint at Oasis Bar.

    This voucher is for one-time use only. Show this QR at the bar to claim your drink.

    Cheers,
    Oasis Bar Team
    """
    if send_email(reg.email, subject, content, attachment=buf, filename="madri-voucher.png"):
        return jsonify({"message": "Registration successful. QR voucher sent via email."}), 200
    else:
        return jsonify({"error": "Failed to send QR code email"}), 500





