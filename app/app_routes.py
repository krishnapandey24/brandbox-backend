from flask import Blueprint
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from . import Config
from .models import User, Product, Order, OrderItem, db, Media, Category

main = Blueprint('main', __name__)



@main.route('/')
def home():
    return "Hello world"


@main.route('/login', methods=['POST'])
def login():
    data = request.json

    email = data.get('email')
    provider = data.get('provider')

    if not email or not provider:
        return jsonify({"error": "Missing email or provider"}), 400

    # Verify the user
    user = User.query.filter_by(email=email, provider=provider).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    # If user is found, generate JWT token
    access_token = create_access_token(identity=user.id)
    return jsonify(access_token=access_token, user={'email': user.email, 'name': user.name}), 200


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

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201


@main.route('/verify', methods=['GET'])
@jwt_required()
def verify():
    current_user_id = get_jwt_identity()
    data = request.json
    user_id= data.get('user_id')
    if current_user_id != user_id:
        return jsonify({"message": current_user_id}), 401
    else:
        return jsonify({"message": "Authorized"}), 200



@main.route('/orders', methods=['POST'])
def place_order():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    user_id= data.get('user_id')

    if current_user_id != user_id:
      return jsonify({"message": "You are not authorized"}), 401

    new_order = Order(user_id=user_id, total_amount=data['total_amount'])
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


@main.route('/products/<int:product_id>', methods=['GET'])
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
        "id": product.product_id,
        "name": product.product_name,
        "description": product.description,
        "price": product.price,
        "created_at": product.created_at,
        "updated_at": product.updated_at,
        "media": media_data
    }

    return jsonify(product_data), 200


@main.route('/products', methods=['POST'])
def add_product():
    data = request.json

    # Extract data from request
    name = data.get('name')
    description = data.get('description')
    price = data.get('price')
    stock_quantity = data.get('stock_quantity')
    category_id = data.get('category_id')

    if not name or not price or not stock_quantity or not category_id:
        return jsonify({"message": "Missing required fields"}), 400

    new_product = Product(
        product_name=name,
        description=description,
        price=price,
        stock_quantity=stock_quantity,
        category_id=category_id
    )

    # Add and commit to the database
    db.session.add(new_product)
    db.session.commit()

    return jsonify({"message": "Product added successfully", "product_id": new_product.product_id}), 201


from flask import request, jsonify
from werkzeug.utils import secure_filename
import os

@main.route('/products/<int:product_id>/media', methods=['POST'])
def add_media(product_id):
    # Check if the product exists
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"message": "Product not found"}), 404

    # Check if a file was uploaded
    if 'file' not in request.files:
        return jsonify({"message": "No file part"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400

    # Validate file type (ensure it's either audio or video)
    is_image=file.content_type.startswith('image/')
    is_video=file.content_type.startswith('video/')
    if file and (is_image or is_video):
        # Save the file
        filename = secure_filename(file.filename)
        file_path = os.path.join(Config.MEDIA_FOLDER, filename)
        file.save(file_path)

        # Create new media record
        new_media = Media(
            product_id=product_id,
            media_type="image" if is_image else "video" ,
            name=filename  # Save the path or URL of the file
        )

        # Add and commit to the database
        db.session.add(new_media)
        db.session.commit()

        return jsonify({"message": "Media added successfully", "media_id": new_media.id}), 201

    return jsonify({"message": "Invalid file type"}), 400


@main.route('/category', methods=['POST'])
def create_category():
    data = request.get_json()

    # Validate the incoming request
    if not data or 'category_name' not in data:
        return jsonify({"error": "Category name is required"}), 400

    # Check if the category already exists
    existing_category = Category.query.filter_by(category_name=data['category_name']).first()
    if existing_category:
        return jsonify({"error": "Category already exists"}), 400

    # Create a new category
    new_category = Category(
        category_name=data['category_name'],
        description=data.get('description')  # Optional field
    )

    try:
        # Add and commit to the database
        db.session.add(new_category)
        db.session.commit()

        return jsonify({"message": "Category created successfully", "category_id": new_category.category_id}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500