from flask import Blueprint, request, jsonify

from .models import User, Product, Order, OrderItem, db, Media

main = Blueprint('main', __name__)
product_bp = Blueprint('product', __name__)



@main.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    result = [
        {
            'product_id': product.product_id,
            'product_name': product.product_name,
            'price': str(product.price),
            'stock_quantity': product.stock_quantity,
        }
        for product in products
    ]
    return jsonify(result)


@main.route('/register', methods=['POST'])
def register():
    data = request.json

    provider = data.get('provider')
    email = data.get('email')
    name = data.get('name')

    if not provider or not email or not name:
        return jsonify({"message": "Missing required fields"}), 400

    # Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"message": "User already registered"}), 400

    # Create a new user
    new_user = User(
        provider=provider,
        email=email,
        name=name,
    )

    # Add and commit to the database
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201


@main.route('/orders', methods=['POST'])
def place_order():
    data = request.get_json()
    new_order = Order(user_id=data['user_id'], total_amount=data['total_amount'])
    db.session.add(new_order)
    db.session.commit()

    for item in data['items']:
        new_order_item = OrderItem(
            order_id=new_order.order_id,
            product_id=item['product_id'],
            quantity=item['quantity'],
            price_at_purchase=item['price_at_purchase']
        )
        db.session.add(new_order_item)

    db.session.commit()
    return jsonify({'message': 'Order placed successfully'}), 201


@product_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product_details(product_id):
    # Retrieve product and associated media
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"message": "Product not found"}), 404

    media_list = Media.query.filter_by(product_id=product_id).all()
    media_data = [
        {
            "id": media.id,
            "media_type": media.media_type,
            "url": media.url
        } for media in media_list
    ]

    product_data = {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "created_at": product.created_at,
        "updated_at": product.updated_at,
        "media": media_data
    }

    return jsonify(product_data), 200