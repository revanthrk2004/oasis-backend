# app/offers.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from .models import Offer, db
from .decorators import admin_required

offers_bp = Blueprint('offers', __name__, url_prefix='/offers')

@offers_bp.route('', methods=['GET'])
def list_offers():
    offers = (
        Offer.query
             .filter_by(active=True)
             .order_by(Offer.sort_order)
             .all()
    )
    return jsonify([{
        "id":         o.id,
        "title":      o.title,
        "subtitle":   o.subtitle,
        "image_url":  o.image_url,
        "bullets":    o.bullets,
        "sort_order": o.sort_order
    } for o in offers]), 200

@offers_bp.route('', methods=['POST'])
@jwt_required()
@admin_required
def create_offer():
    data = request.get_json() or {}
    if not data.get("title"):
        return jsonify({"error": "Title is required"}), 400

    new = Offer(
        title      = data["title"],
        subtitle   = data.get("subtitle", ""),
        image_url  = data.get("image_url", ""),
        bullets    = data.get("bullets", []),
        sort_order = data.get("sort_order", 0),
        active     = data.get("active", True)
    )
    db.session.add(new)
    db.session.commit()
    return jsonify({"id": new.id}), 201

@offers_bp.route('/<int:offer_id>', methods=['PATCH'])
@jwt_required()
@admin_required
def update_offer(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    data = request.get_json() or {}
    for field in ("title","subtitle","image_url","bullets","sort_order","active"):
        if field in data:
            setattr(offer, field, data[field])
    db.session.commit()
    return jsonify({"message": "Offer updated"}), 200

@offers_bp.route('/<int:offer_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_offer(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    db.session.delete(offer)
    db.session.commit()
    return jsonify({"message": "Offer deleted"}), 200
