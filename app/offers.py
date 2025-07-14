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
    return jsonify([o.to_dict() for o in offers]), 200


@offers_bp.route('', methods=['POST'])
@jwt_required()
@admin_required
def create_offer():
    data = request.get_json(force=True) or {}

    title     = data.get("title")
    image_url = data.get("image_url")
    bullets   = data.get("bullets", [])

    if not title or not image_url:
        return jsonify({"error": "Title and image_url are required"}), 400

    if not isinstance(bullets, list):
        return jsonify({"error": "bullets must be an array"}), 400

    new = Offer(
        title      = title,
        subtitle   = data.get("subtitle", ""),
        image_url  = image_url,
        bullets    = bullets,               # <-- plain Python list
        sort_order = data.get("sort_order", 0),
        active     = data.get("active", True),
    )

    db.session.add(new)
    db.session.commit()
    return jsonify({"id": new.id}), 201


@offers_bp.route('/<int:offer_id>', methods=['PATCH'])
@jwt_required()
@admin_required
def update_offer(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    data = request.get_json(force=True) or {}

    # update simple fields
    for field in ("title", "subtitle", "image_url", "sort_order", "active"):
        if field in data:
            setattr(offer, field, data[field])

    # update bullets
    if "bullets" in data:
        raw = data["bullets"]
        if not isinstance(raw, list):
            return jsonify({"error": "bullets must be an array"}), 400
        offer.bullets = raw  # <-- again, just a list

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
