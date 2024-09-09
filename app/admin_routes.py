from flask import Blueprint, request, jsonify
from .models import Product, db, Media

products_bp = Blueprint('products', __name__)
media_bp = Blueprint('media', __name__)


@products_bp.route('/products', methods=['POST'])
def add_product():
    data = request.json

    # Extract data from request
    name = data.get('name')
    description = data.get('description')
    price = data.get('price')

    if not name or not price:
        return jsonify({"message": "Missing required fields"}), 400

    # Create a new product
    new_product = Product(
        name=name,
        description=description,
        price=price
    )

    # Add and commit to the database
    db.session.add(new_product)
    db.session.commit()

    return jsonify({"message": "Product added successfully", "product_id": new_product.id}), 201


@media_bp.route('/products/<int:product_id>/media', methods=['POST'])
def add_media(product_id):
    data = request.json

    # Extract data from request
    media_type = data.get('media_type')
    url = data.get('url')

    if not media_type or not url or media_type not in ['image', 'video']:
        return jsonify({"message": "Invalid media type or missing fields"}), 400

    # Check if the product exists
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"message": "Product not found"}), 404

    # Create new media record
    new_media = Media(
        product_id=product_id,
        media_type=media_type,
        url=url
    )

    # Add and commit to the database
    db.session.add(new_media)
    db.session.commit()

    return jsonify({"message": "Media added successfully", "media_id": new_media.id}), 201


