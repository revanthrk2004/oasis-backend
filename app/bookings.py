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

    required_fields = ["date", "time", "end_time", "guest_count", "table_number"]
    if not data or not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required booking fields"}), 400

    try:
        booking_time = datetime.strptime(f"{data['date']} {data['time']}", "%Y-%m-%d %H:%M")
        end_time = datetime.strptime(f"{data['date']} {data['end_time']}", "%Y-%m-%d %H:%M")

        if end_time <= booking_time:
            return jsonify({"error": "End time must be after start time"}), 400

        # Check for overlapping bookings on the same table
        overlapping = Booking.query.filter(
            Booking.table_number == data["table_number"],
            Booking.booking_time < end_time,
            Booking.end_time > booking_time
        ).first()

        if overlapping:
            return jsonify({"error": "Time slot already booked for this table"}), 409

        booking = Booking(
            user_id=user_id,
            table_number=data["table_number"],
            booking_time=booking_time,
            end_time=end_time,
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
        "start_time": b.booking_time.strftime("%H:%M"),
        "end_time": b.end_time.strftime("%H:%M"),
        "guest_count": b.guest_count,
        "table_number": b.table_number,
        "note": b.note
    } for b in user_bookings]), 200

# GET /bookings/check - Check if a booking already exists for the time and table type
@bookings.route('/bookings/check', methods=['GET'])
@jwt_required()
def check_booking_conflict():
    date = request.args.get('date')
    time = request.args.get('time')
    end_time_str = request.args.get('end_time')
    table_number = request.args.get('table_number')

    if not date or not time or not end_time_str or not table_number:
        return jsonify({"error": "Missing parameters"}), 400

    try:
        booking_time = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        end_time = datetime.strptime(f"{date} {end_time_str}", "%Y-%m-%d %H:%M")

        existing = Booking.query.filter(
            Booking.table_number == table_number,
            Booking.booking_time < end_time,
            Booking.end_time > booking_time
        ).first()

        return jsonify({"conflict": bool(existing)}), 200

    except Exception as e:
        return jsonify({"error": f"Invalid request: {str(e)}"}), 500
