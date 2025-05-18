# app/routes.py
from flask import Blueprint, jsonify, current_app

main = Blueprint('main', __name__)

@main.route('/')
def home():
    try:
        return jsonify({"message": "API is live!"})
    except Exception as e:
        current_app.logger.error(f"Home route error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
