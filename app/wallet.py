from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import db, User, WalletTransaction
from datetime import datetime
import stripe
import os

wallet = Blueprint('wallet', __name__)

# ✅ Set Stripe secret key from environment
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# GET /wallet - Get current balance
@wallet.route('/wallet', methods=['GET'])
@jwt_required()
def get_wallet_balance():
    user = User.query.get(get_jwt_identity())
    balance = user.wallet_balance or 0.0
    return jsonify({"balance": round(balance, 2)})

# POST /wallet/topup - Add funds manually
@wallet.route('/wallet/topup', methods=['POST'])
@jwt_required()
def top_up_wallet():
    user = User.query.get(get_jwt_identity())
    data = request.get_json()
    amount = data.get("amount", 0)

    if amount <= 0:
        return jsonify({"error": "Invalid top-up amount"}), 400

    user.wallet_balance = (user.wallet_balance or 0.0) + amount

    tx = WalletTransaction(
        user_id=user.id,
        amount=amount,
        type="topup",
        description=data.get("description", "Top-up")
    )
    db.session.add(tx)
    db.session.commit()

    return jsonify({"message": "Wallet topped up successfully", "new_balance": round(user.wallet_balance, 2)})

# GET /wallet/history - View transaction history
@wallet.route('/wallet/history', methods=['GET'])
@jwt_required()
def view_transaction_history():
    user_id = get_jwt_identity()
    transactions = WalletTransaction.query.filter_by(user_id=user_id).order_by(WalletTransaction.timestamp.desc()).all()
    return jsonify([
        {
            "id": tx.id,
            "amount": tx.amount,
            "type": tx.type,
            "description": tx.description,
            "timestamp": tx.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        } for tx in transactions
    ])

# ✅ POST /wallet/stripe-intent - Create Stripe payment intent
@wallet.route('/wallet/stripe-intent', methods=['POST'])
@jwt_required()
def create_stripe_payment_intent():
    user_id = get_jwt_identity()
    data = request.get_json()
    amount = data.get("amount")

    if not amount or amount <= 0:
        return jsonify({"error": "Invalid amount"}), 400

    try:
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # convert to pence
            currency='gbp',
            metadata={"user_id": user_id}
        )
        return jsonify({"client_secret": intent.client_secret})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
