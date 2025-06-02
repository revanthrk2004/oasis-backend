from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from .models import db, HappyHourRule
from .decorators import admin_required
from datetime import time

happy_hour = Blueprint('happy_hour', __name__)

# GET all rules
@happy_hour.route('/admin/happy-hour', methods=['GET'])
@jwt_required()
@admin_required
def list_happy_hours():
    rules = HappyHourRule.query.all()
    return jsonify([
        {
            "id": rule.id,
            "start_time": rule.start_time.strftime("%H:%M"),
            "end_time": rule.end_time.strftime("%H:%M"),
            "discount_percent": rule.discount_percent,
            "days_active": rule.days_active
        } for rule in rules
    ])

# POST a new rule
@happy_hour.route('/admin/happy-hour', methods=['POST'])
@jwt_required()
@admin_required
def add_happy_hour():
    data = request.get_json()
    try:
        rule = HappyHourRule(
            start_time=time.fromisoformat(data["start_time"]),
            end_time=time.fromisoformat(data["end_time"]),
            discount_percent=int(data.get("discount_percent", 0)),
            deal_description=data.get("deal_description", ""),
            days_active=",".join(data["days_active"])
        )
        db.session.add(rule)
        db.session.commit()
        return jsonify({"message": "Happy Hour rule added"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# PATCH update rule
@happy_hour.route('/admin/happy-hour/<int:rule_id>', methods=['PATCH'])
@jwt_required()
@admin_required
def update_happy_hour(rule_id):
    rule = HappyHourRule.query.get(rule_id)
    if not rule:
        return jsonify({"error": "Rule not found"}), 404

    data = request.get_json()
    try:
        if "start_time" in data:
            rule.start_time = time.fromisoformat(data["start_time"])
        if "end_time" in data:
            rule.end_time = time.fromisoformat(data["end_time"])
        if "discount_percent" in data:
            rule.discount_percent = int(data["discount_percent"])
        if "days_active" in data:
            rule.days_active = data["days_active"]
        
        db.session.commit()
        return jsonify({"message": "Rule updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# DELETE a rule
@happy_hour.route('/admin/happy-hour/<int:rule_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_happy_hour(rule_id):
    rule = HappyHourRule.query.get(rule_id)
    if not rule:
        return jsonify({"error": "Rule not found"}), 404

    db.session.delete(rule)
    db.session.commit()
    return jsonify({"message": "Rule deleted"}), 200
