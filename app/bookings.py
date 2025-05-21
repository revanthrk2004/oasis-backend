from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import db, Booking
from datetime import datetime

bookings = Blueprint('bookings', __name__)

# POST /bookings - Create a new booking
@bookings.route('/bookings', methods=['POST'])
@jwt_required()
def create_booking():
    user_id = get_jwt_identity()
    data = request.get_json()

    required_fields = ["date", "time", "guest_count", "table_number"]
    if not data or not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required booking fields"}), 400

    try:
        booking_time = datetime.strptime(f"{data['date']} {data['time']}", "%Y-%m-%d %H:%M")
        booking = Booking(
            user_id=user_id,
            table_number=data["table_number"],
            booking_time=booking_time,
            guest_count=int(data["guest_count"]),
            note=data.get("note")
        )
        db.session.add(booking)
        db.session.commit()
        return jsonify({"message": "Booking created successfully"}), 201
    except Exception as e:
        return jsonify({"error": f"Failed to create booking: {str(e)}"}), 500

# GET /bookings - View all bookings of current user
@bookings.route('/bookings', methods=['GET'])
@jwt_required()
def view_bookings():
    user_id = get_jwt_identity()
    user_bookings = Booking.query.filter_by(user_id=user_id).all()
    return jsonify([{
        "id": b.id,
        "date": b.booking_time.strftime("%Y-%m-%d"),
        "time": b.booking_time.strftime("%H:%M"),
        "guest_count": b.guest_count,
        "table_number": b.table_number,
        "note": b.note
    } for b in user_bookings]), 200
