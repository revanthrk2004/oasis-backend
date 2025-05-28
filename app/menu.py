from flask import Blueprint, request, jsonify
from .models import MenuItem, HappyHourRule, db
from flask_jwt_extended import jwt_required
from .decorators import admin_required
from datetime import datetime

menu = Blueprint('menu', __name__)

def get_current_discount_rule():
    now = datetime.now()
    current_day = now.strftime('%a')
    current_time = now.time()

    rules = HappyHourRule.query.all()
    for rule in rules:
        if (current_day in rule.days_active.split(',')) and (rule.start_time <= current_time <= rule.end_time):
            return rule
    return None

@menu.route('/menu', methods=['GET'])
def get_menu():
    rule = get_current_discount_rule()
    items = MenuItem.query.all()

    result = []
    for item in items:
        original_price = item.price
        discounted_price = original_price
        discount_applied = None

        if rule and item.category.lower() == 'cocktails' and item.is_happy_hour_eligible:
            # Pricing for 2 cocktails = £15 => per unit = £7.50
            discounted_price = 7.50
            discount_applied = "2 for £15"

        result.append({
            "id": item.id,
            "name": item.name,
            "description": item.description,
            "price": round(discounted_price, 2),
            "original_price": round(original_price, 2),
            "discount_applied": discount_applied,
            "category": item.category,
            "image_url": item.image_url or ""
        })

    return jsonify(result)

@menu.route('/menu', methods=['POST'])
@jwt_required()
@admin_required
def add_menu_item():
    data = request.get_json()
    item = MenuItem(
        name=data.get('name'),
        description=data.get('description'),
        price=data.get('price'),
        category=data.get('category'),
        image_url=data.get('image_url'),
        is_happy_hour_eligible=data.get('is_happy_hour_eligible', False)
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({"message": "Menu item added"}), 201

@menu.route('/menu/<int:item_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_menu_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Item deleted"}), 200
