from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import db, CartItem, Order, OrderItem, MenuItem

orders = Blueprint('orders', __name__)

@orders.route('/cart', methods=['POST'])
@jwt_required()
def add_to_cart():
    user_id = get_jwt_identity()
    data = request.get_json()
    menu_item_id = data.get("item_id")  # This is what the user sends
    quantity = data.get("quantity", 1)

    item = MenuItem.query.get(menu_item_id)
    if not item:
        return jsonify({"error": "Item not found"}), 404

    cart_item = CartItem(user_id=user_id, menu_item_id=menu_item_id, quantity=quantity)
    db.session.add(cart_item)
    db.session.commit()
    return jsonify({"message": "Item added to cart"}), 201

@orders.route('/cart', methods=['GET'])
@jwt_required()
def view_cart():
    user_id = get_jwt_identity()
    cart = CartItem.query.filter_by(user_id=user_id).all()
    return jsonify([
        {
            "id": item.id,
            "item": item.menu_item.name,
            "quantity": item.quantity
        } for item in cart
    ])

@orders.route('/orders', methods=['POST'])
@jwt_required()
def checkout():
    user_id = get_jwt_identity()
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    if not cart_items:
        return jsonify({"error": "Cart is empty"}), 400

    total = sum(item.menu_item.price * item.quantity for item in cart_items)
    order = Order(user_id=user_id, total=total)
    db.session.add(order)
    db.session.flush()

    for item in cart_items:
        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=item.menu_item_id,
            quantity=item.quantity
        )
        db.session.add(order_item)
        db.session.delete(item)

    db.session.commit()
    return jsonify({"message": "Order placed successfully"}), 201

@orders.route('/orders', methods=['GET'])
@jwt_required()
def view_orders():
    user_id = get_jwt_identity()
    orders = Order.query.filter_by(user_id=user_id).all()
    return jsonify([
        {
            "order_id": order.id,
            "items": [
                {
                    "name": item.menu_item.name,
                    "quantity": item.quantity
                } for item in order.items
            ]
        } for order in orders
    ])
