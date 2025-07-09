from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from .models import db, Offer
import json

offers_bp = Blueprint('offers', __name__, url_prefix='/offers')

def admin_only():
    claims = get_jwt()
    if claims.get("role") != "admin":
        return False
    return True

@offers_bp.route('', methods=['GET'])
def list_offers():
    # Public endpoint: show only active sorted
    offers = Offer.query.filter_by(active=True).order_by(Offer.sort_order).all()
    return jsonify([o.to_dict() for o in offers]), 200

@offers_bp.route('', methods=['POST'])
@jwt_required()
def create_offer():
    if not admin_only(): return jsonify({"error":"Admin only"}), 403
    data = request.get_json()
    o = Offer(
      title=data['title'],
      subtitle=data.get('subtitle',''),
      image_url=data.get('image_url',''),
      bullets=json.dumps(data.get('bullets',[])),
      sort_order=data.get('sort_order',0),
      active=data.get('active',True)
    )
    db.session.add(o); db.session.commit()
    return jsonify(o.to_dict()), 201

@offers_bp.route('/<int:oid>', methods=['PATCH'])
@jwt_required()
def update_offer(oid):
    if not admin_only(): return jsonify({"error":"Admin only"}), 403
    data = request.get_json()
    o = Offer.query.get_or_404(oid)
    for k in ('title','subtitle','image_url','sort_order','active'):
      if k in data: setattr(o, k, data[k])
    if 'bullets' in data: o.bullets = json.dumps(data['bullets'])
    db.session.commit()
    return jsonify(o.to_dict()), 200

@offers_bp.route('/<int:oid>', methods=['DELETE'])
@jwt_required()
def delete_offer(oid):
    if not admin_only(): return jsonify({"error":"Admin only"}), 403
    o = Offer.query.get_or_404(oid)
    db.session.delete(o); db.session.commit()
    return jsonify({"message":"Deleted"}), 200
