from flask import Blueprint, request, jsonify
from .models import MenuItem, db
from flask_jwt_extended import jwt_required
from .decorators import admin_required

menu = Blueprint('menu', __name__)

# GET all menu items
@menu.route('/menu', methods=['GET'])
def get_menu():
    items = MenuItem.query.all()
    return jsonify([{
        "id": item.id,
        "name": item.name,
        "description": item.description,
        "price": item.price,
        "category": item.category
    } for item in items])

# POST a new menu item (admin only)
@menu.route('/menu', methods=['POST'])
@jwt_required()
@admin_required
def add_menu_item():
    data = request.get_json()
    item = MenuItem(**data)
    db.session.add(item)
    db.session.commit()
    return jsonify({"message": "Menu item added"}), 201

# DELETE a menu item (admin only)
@menu.route('/menu/<int:item_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_menu_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Item deleted"}), 200
