from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from .models import db, User, Order, Booking, OpenTab, OrderItem, MenuItem, HappyHourRule, AppSetting
from sqlalchemy.sql import func
from .decorators import admin_required

admin = Blueprint('admin', __name__)

@admin.route('/admin/metrics', methods=['GET'])
@jwt_required()
@admin_required
def admin_metrics():
    user_subq = db.session.query(User.id).filter(User.role != 'admin').subquery()

    total_revenue = db.session.query(func.sum(Order.total)).filter(Order.user_id.in_(user_subq)).scalar() or 0
    total_orders = Order.query.filter(Order.user_id.in_(user_subq)).count()
    total_bookings = Booking.query.filter(Booking.user_id.in_(user_subq)).count()
    total_tabs = OpenTab.query.filter(OpenTab.user_id.in_(user_subq)).count()

    today = func.current_date()
    daily_revenue = db.session.query(func.sum(Order.total)).filter(Order.user_id.in_(user_subq), func.date(Order.created_at) == today).scalar() or 0
    daily_orders = Order.query.filter(Order.user_id.in_(user_subq), func.date(Order.created_at) == today).count()
    daily_bookings = Booking.query.filter(Booking.user_id.in_(user_subq), func.date(Booking.created_at) == today).count()

    return jsonify({
        "total_revenue": round(total_revenue, 2),
        "total_orders": total_orders,
        "total_bookings": total_bookings,
        "total_tabs": total_tabs,
        "today": {
            "revenue": round(daily_revenue, 2),
            "orders": daily_orders,
            "bookings": daily_bookings
        }
    })

@admin.route('/admin/top-customers', methods=['GET'])
@jwt_required()
@admin_required
def top_customers():
    results = (
        db.session.query(
            User.id,
            User.username,
            func.sum(Order.total).label("total_spent")
        )
        .join(Order, User.id == Order.user_id)
        .filter(User.role != 'admin')
        .group_by(User.id)
        .order_by(func.sum(Order.total).desc())
        .limit(10)
        .all()
    )

    return jsonify([
        {
            "user_id": user.id,
            "username": user.username,
            "total_spent": round(user.total_spent, 2)
        } for user in results
    ])

@admin.route('/admin/user-tabs/<int:user_id>', methods=['GET'])
@jwt_required()
@admin_required
def view_user_tabs(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    tabs = OpenTab.query.filter_by(user_id=user_id).order_by(OpenTab.started_at.desc()).all()

    return jsonify([{
        "tab_id": tab.id,
        "total": round(tab.total, 2),
        "is_open": tab.is_open,
        "started_at": tab.started_at.strftime("%Y-%m-%d %H:%M:%S")
    } for tab in tabs]), 200

@admin.route('/admin/user-orders/<int:user_id>', methods=['GET'])
@jwt_required()
@admin_required
def view_user_orders(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()

    return jsonify([
        {
            "order_id": order.id,
            "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "total": round(order.total, 2),
            "items": [
                {
                    "name": item.menu_item.name,
                    "quantity": item.quantity
                } for item in order.items
            ]
        } for order in orders
    ]), 200

@admin.route('/admin/user-bookings/<int:user_id>', methods=['GET'])
@jwt_required()
@admin_required
def view_user_bookings(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    bookings = Booking.query.filter_by(user_id=user_id).order_by(Booking.booking_time.desc()).all()

    return jsonify([{
        "booking_id": b.id,
        "table_number": b.table_number,
        "guest_count": b.guest_count,
        "booking_time": b.booking_time.strftime("%Y-%m-%d %H:%M"),
        "note": b.note
    } for b in bookings]), 200

@admin.route('/admin/happy-hour-metrics', methods=['GET'])
@jwt_required()
@admin_required
def happy_hour_metrics():
    from datetime import datetime
    from sqlalchemy import extract
    import pytz

    london = pytz.timezone("Europe/London")
    now = datetime.now(london)
    current_day = now.strftime('%a')
    rules = HappyHourRule.query.filter(HappyHourRule.days_active.ilike(f"%{current_day}%")).all()

    if not rules:
        return jsonify({"message": "No active Happy Hour rules for today"}), 200

    total_orders = 0
    total_revenue = 0.0
    total_discount_saved = 0.0
    item_sales = {}

    for rule in rules:
        start_of_day = datetime(now.year, now.month, now.day, tzinfo=london)
        all_orders = (
            Order.query
            .join(User)
            .filter(
                User.role != 'admin',
                Order.created_at >= start_of_day
            )
            .all()
        )

        for order in all_orders:
            order_time = order.created_at if order.created_at.tzinfo else london.localize(order.created_at)
            if rule.start_time <= order_time.time() <= rule.end_time:
                total_orders += 1
                total_revenue += order.total

                for item in order.items:
                    full_price = item.menu_item.price * item.quantity
                    discounted_price = full_price * (1 - rule.discount_percent / 100)
                    saved = full_price - discounted_price

                    total_discount_saved += saved
                    name = item.menu_item.name
                    item_sales[name] = item_sales.get(name, 0) + item.quantity

    top_items = sorted(item_sales.items(), key=lambda x: x[1], reverse=True)

    return jsonify({
        "happy_hour_orders": total_orders,
        "happy_hour_revenue": round(total_revenue, 2),
        "total_discount_saved": round(total_discount_saved, 2),
        "top_discounted_items": [{"name": k, "quantity": v} for k, v in top_items[:5]]
    }), 200

@admin.route('/admin/settings', methods=['GET'])
@jwt_required()
@admin_required
def get_settings():
    settings = AppSetting.query.all()
    return jsonify({s.key: s.value for s in settings}), 200

@admin.route('/admin/settings', methods=['POST'])
@jwt_required()
@admin_required
def update_setting():
    data = request.get_json()
    key = data.get("key")
    value = data.get("value")

    if not key or not value:
        return jsonify({"error": "Missing 'key' or 'value'"}), 400

    setting = AppSetting.query.filter_by(key=key).first()
    if setting:
        setting.value = value
    else:
        setting = AppSetting(key=key, value=value)
        db.session.add(setting)

    db.session.commit()
    return jsonify({"message": f"Setting '{key}' saved.", "value": value}), 200

@admin.route('/settings/public', methods=['GET'])
def public_settings():
    allowed_keys = ['business_hours', 'contact_email', 'contact_number', 'announcement_banner']
    settings = AppSetting.query.filter(AppSetting.key.in_(allowed_keys)).all()
    return jsonify({s.key: s.value for s in settings}), 200

@admin.route('/admin/scan-user/<oasis_card_id>', methods=['GET'])
@jwt_required()
@admin_required
def scan_user_profile(oasis_card_id):
    user = User.query.filter_by(oasis_card_id=oasis_card_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "wallet_balance": round(user.wallet_balance, 2),
        "oasis_card_id": user.oasis_card_id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone": user.phone,
        "address": user.address
    }), 200

@admin.route('/admin/bookings', methods=['GET'])
@jwt_required()
@admin_required
def admin_all_bookings():
    bookings = Booking.query.order_by(Booking.booking_time.desc()).all()
    return jsonify([
        {
            "id": b.id,
            "user_name": b.user.username if b.user else None,
            "table_number": b.table_number,
            "guest_count": b.guest_count,
            "start_time": b.booking_time.isoformat() if b.booking_time else None,

            "end_time": b.end_time.isoformat() if b.end_time else None,
            "note": b.note
        } for b in bookings
    ])

@admin.route('/admin/bookings/<int:booking_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def admin_cancel_booking(booking_id):
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({"error": "Booking not found"}), 404

    db.session.delete(booking)
    db.session.commit()
    return jsonify({"message": "Booking cancelled by admin"}), 200
