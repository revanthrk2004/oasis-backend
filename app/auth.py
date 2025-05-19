from flask import Blueprint, request, jsonify
from .models import User, db
from flask_jwt_extended import create_access_token
from sqlalchemy.exc import IntegrityError
from datetime import timedelta

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not all(k in data for k in ("username", "email", "password")):
        return jsonify({"error": "Missing required fields"}), 400

    user = User(username=data["username"], email=data["email"])
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
        access_token = create_access_token(identity=str(user.id), additional_claims={"role": user.role}, expires_delta=timedelta(days=365))

        return jsonify(access_token=access_token), 200

    return jsonify({"error": "Invalid credentials"}), 401

