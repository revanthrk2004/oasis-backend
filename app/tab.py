from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import db, OpenTab, MenuItem, User, WalletTransaction
from datetime import datetime

tab = Blueprint('tab', __name__)

# POST /tab/open
@tab.route('/tab/open', methods=['POST'])
@jwt_required()
def open_tab():
    user_id = get_jwt_identity()
    existing_tab = OpenTab.query.filter_by(user_id=user_id, is_open=True).first()
    if existing_tab:
        return jsonify({"message": "Tab already open"}), 400

    new_tab = OpenTab(user_id=user_id)
    db.session.add(new_tab)
    db.session.commit()
    return jsonify({"message": "Tab opened", "tab_id": new_tab.id}), 201

# POST /tab/add
@tab.route('/tab/add', methods=['POST'])
@jwt_required()
def add_to_tab():
    user_id = get_jwt_identity()
    data = request.get_json()
    item_id = data.get("item_id")
    quantity = data.get("quantity", 1)

    tab = OpenTab.query.filter_by(user_id=user_id, is_open=True).first()
    if not tab:
        return jsonify({"error": "No open tab"}), 400

    item = MenuItem.query.get(item_id)
    if not item:
        return jsonify({"error": "Item not found"}), 404

    cost = item.price * quantity
    tab.total += cost
    db.session.commit()

    return jsonify({"message": "Item added to tab", "new_total": round(tab.total, 2)}), 200

# GET /tab
@tab.route('/tab', methods=['GET'])
@jwt_required()
def view_tab():
    user_id = get_jwt_identity()
    tab = OpenTab.query.filter_by(user_id=user_id, is_open=True).first()
    if not tab:
        return jsonify({"message": "No open tab"}), 200

    return jsonify({
        "tab_id": tab.id,
        "started_at": tab.started_at.strftime("%Y-%m-%d %H:%M:%S"),
        "total": round(tab.total, 2)
    })

# POST /tab/close
@tab.route('/tab/close', methods=['POST'])
@jwt_required()
def close_tab():
    user_id = get_jwt_identity()
    tab = OpenTab.query.filter_by(user_id=user_id, is_open=True).first()
    if not tab:
        return jsonify({"error": "No open tab"}), 400

    user = User.query.get(user_id)
    if user.wallet_balance < tab.total:
        return jsonify({"error": "Insufficient wallet balance"}), 400

    # Deduct from wallet
    user.wallet_balance -= tab.total

    # Log transaction
    tx = WalletTransaction(
        user_id=user.id,
        amount=tab.total,
        type="deduct",
        description="Tab settlement"
    )
    db.session.add(tx)

    # Close tab
    tab.is_open = False
    db.session.commit()

    return jsonify({
        "message": "Tab closed and paid",
        "final_total": round(tab.total, 2),
        "new_balance": round(user.wallet_balance, 2)
    }), 200

# GET /tab/status/<tab_id>
@tab.route('/tab/status/<int:tab_id>', methods=['GET'])
@jwt_required()
def tab_status(tab_id):
    tab = OpenTab.query.get(tab_id)
    if not tab:
        return jsonify({"error": "Tab not found"}), 404

    return jsonify({
        "tab_id": tab.id,
        "user_id": tab.user_id,
        "is_open": tab.is_open,
        "started_at": tab.started_at.strftime("%Y-%m-%d %H:%M:%S") if tab.started_at else None,
        "total": round(tab.total, 2)
    }), 200

# ✅ NEW: GET /tab/history - List all closed tabs for the user
@tab.route('/tab/history', methods=['GET'])
@jwt_required()
def tab_history():
    user_id = get_jwt_identity()
    closed_tabs = OpenTab.query.filter_by(user_id=user_id, is_open=False).order_by(OpenTab.started_at.desc()).all()

    return jsonify([
        {
            "tab_id": tab.id,
            "total": round(tab.total, 2),
            "started_at": tab.started_at.strftime("%Y-%m-%d %H:%M:%S"),
        } for tab in closed_tabs
    ]), 200
