from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

import json

from sqlalchemy.dialects.postgresql import JSONB 

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'user' or 'admin'
    oasis_card_id = db.Column(db.String(64), unique=True, nullable=True)
    wallet_balance = db.Column(db.Float, default=0.0)

    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class WalletTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'topup' or 'deduct'
    description = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='wallet_transactions')


class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(300))
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100))
    image_url = db.Column(db.String(300))  # link or fallback
    is_happy_hour_eligible = db.Column(db.Boolean, default=False)  # ✅ NEW


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    user = db.relationship('User', backref='cart_items')
    menu_item = db.relationship('MenuItem')


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Float, nullable=False)

    user = db.relationship('User', backref='orders')


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    menu_item_id = db.Column(
        db.Integer,
        db.ForeignKey('menu_item.id', ondelete='CASCADE'),
        nullable=False
    )
    quantity = db.Column(db.Integer, nullable=False)

    order = db.relationship('Order', backref='items')
    menu_item = db.relationship('MenuItem', passive_deletes=True)


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    table_number = db.Column(db.String(10), nullable=False)
    booking_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)  # ✅ NEW FIELD
    guest_count = db.Column(db.Integer, nullable=False)
    note = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='bookings')


class OpenTab(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total = db.Column(db.Float, default=0.0)
    is_open = db.Column(db.Boolean, default=True)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='open_tabs')


class HappyHourRule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    discount_percent = db.Column(db.Float, nullable=False)
    deal_description = db.Column(db.String(100), nullable=True)
    days_active = db.Column(db.String(100), nullable=False)  # increased from 20 to 100

    def is_active_now(self):
        now = datetime.now()
        current_time = now.time()
        current_day = now.strftime('%A')  # make sure to match full day name (e.g., "Monday")
        return (
            self.start_time <= current_time <= self.end_time and
            current_day in self.days_active
        )


class AppSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String(500), nullable=False)



class Coupon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(64), unique=True, nullable=False)  # From VoucherRegistration.voucher_id
    scanned_at = db.Column(db.DateTime, default=datetime.utcnow)
    redeemed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='scanned_coupons')

    # Duplicated user details from VoucherRegistration
    first_name = db.Column(db.String(50))
    middle_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    dob = db.Column(db.Date)
    house_number = db.Column(db.String(20))
    street = db.Column(db.String(100))
    city = db.Column(db.String(50))
    county = db.Column(db.String(50))
    postcode = db.Column(db.String(20))
    country = db.Column(db.String(50))

    raw_data = db.Column(db.Text)  # Optional: JSON snapshot


class ChatLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    flagged = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='chat_logs')


import uuid
from datetime import datetime

class VoucherRegistration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    voucher_id = db.Column(db.String(64), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))

    first_name = db.Column(db.String(50), nullable=False)
    middle_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    dob = db.Column(db.Date, nullable=False)

    house_number = db.Column(db.String(20), nullable=False)
    street = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    county = db.Column(db.String(50), nullable=False)
    postcode = db.Column(db.String(20), nullable=False)
    country = db.Column(db.String(50), nullable=False)

    consent_given = db.Column(db.Boolean, default=False)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    used_at = db.Column(db.DateTime, nullable=True)



class Offer(db.Model):
    __tablename__ = 'offers'
    id         = db.Column(db.Integer, primary_key=True)
    title      = db.Column(db.String(100), nullable=False)
    subtitle   = db.Column(db.String(100), nullable=True)
    image_url  = db.Column(db.String(500), nullable=False)       # ← store Cloudinary URL
    bullets    = db.Column(JSONB, nullable=False, default=list)  # ← real JSON column
    sort_order = db.Column(db.Integer, default=0)
    active     = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            "id":         self.id,
            "title":      self.title,
            "subtitle":   self.subtitle,
            "image_url":  self.image_url,
            "bullets":    self.bullets,
            "sort_order": self.sort_order,
            "active":     self.active,
        }
