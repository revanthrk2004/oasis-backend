from flask import Blueprint, request, jsonify
from .models import MenuItem, HappyHourRule, db
from flask_jwt_extended import jwt_required
from .decorators import admin_required
from datetime import datetime

menu = Blueprint('menu', __name__)

def get_current_discount():
    now = datetime.now()
    current_day = now.strftime('%a')  # 'Mon', 'Tue', etc.
    current_time = now.time()

    rules = HappyHourRule.query.all()
    for rule in rules:
        if (current_day in rule.days_active.split(',')) and (rule.start_time <= current_time <= rule.end_time):
            return rule.discount_percent
    return 0

# ✅ GET all menu items (with discount + image_url)
@menu.route('/menu', methods=['GET'])
def get_menu():
    discount_percent = get_current_discount()
    items = MenuItem.query.all()

    result = []
    for item in items:
        original_price = item.price
        discounted_price = original_price * (1 - discount_percent / 100) if discount_percent else original_price

        result.append({
            "id": item.id,
            "name": item.name,
            "description": item.description,
            "price": round(discounted_price, 2),
            "original_price": round(original_price, 2),
            "discount_applied": f"{discount_percent}%" if discount_percent else None,
            "category": item.category,
            "image_url": item.image_url or ""  # ✅ Include image_url
        })

    return jsonify(result)

# ✅ POST a new menu item (admin only)
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
        image_url=data.get('image_url')  # ✅ Handle image URL on POST
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({"message": "Menu item added"}), 201

# ✅ DELETE a menu item (admin only)
@menu.route('/menu/<int:item_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_menu_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Item deleted"}), 200
