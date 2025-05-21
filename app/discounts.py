from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from .models import db, HappyHourRule
from .decorators import admin_required
from datetime import time

discounts = Blueprint('discounts', __name__)

# Admin: Create new happy hour rule
@discounts.route('/admin/happy-hour', methods=['POST'])
@jwt_required()
@admin_required
def create_happy_hour():
    data = request.get_json()
    try:
        rule = HappyHourRule(
            start_time=time.fromisoformat(data["start_time"]),
            end_time=time.fromisoformat(data["end_time"]),
            discount_percent=float(data["discount_percent"]),
            days_active=data["days_active"]  # e.g., "Mon,Tue,Fri"
        )
        db.session.add(rule)
        db.session.commit()
        return jsonify({"message": "Happy Hour rule created"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Public: Check if happy hour is on now
@discounts.route('/happy-hour/status', methods=['GET'])
def check_happy_hour():
    from datetime import datetime
    now = datetime.now()
    day = now.strftime('%a')
    current_time = now.time()
    active_rules = HappyHourRule.query.all()

    for rule in active_rules:
        if (day in rule.days_active.split(',')) and (rule.start_time <= current_time <= rule.end_time):
            return jsonify({
                "active": True,
                "discount_percent": rule.discount_percent
            })

    return jsonify({"active": False})
