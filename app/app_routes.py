from datetime import datetime

from MySQLdb import IntegrityError
from flask import Blueprint, send_from_directory, current_app, abort
from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from sqlalchemy import func

from .models import User, Product, Order, OrderItem, db, Media, Variant, CartItem, Cart, Saved, SavedItem

main = Blueprint('main', __name__)


@main.route('/')
def home():
    return "Hello world"

@main.route('/media/<path:filename>')
def serve_media(filename):
    try:
        return send_from_directory(current_app.config['MEDIA_FOLDER'], filename)
    except FileNotFoundError:
        abort(404)



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


@main.route('/all_products', methods=['GET'])
def get_all_products():
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


@main.route('/products', methods=['GET'])
def get_products():
    # Get query parameters
    category_id = request.args.get('category_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    sort_by = request.args.get('sort_by', 'created_at')  # Default to 'created_at'
    sort_order = request.args.get('sort_order', 'asc')  # Default to ascending (asc)
    feature_type = request.args.get('feature_type')  # If feature_type is provided
    gender = request.args.get('gender')

    # Map allowed fields for sorting
    sortable_fields = {
        'sales': Product.sales,
        'price': Product.price,
        'reviews': Product.total_reviews,
        'created': Product.created_at
    }

    # Validate sort_by field
    if sort_by not in sortable_fields:
        return jsonify({'error': 'Invalid sort field'}), 400

    # Set the sorting order (asc or desc)
    sort_func = sortable_fields[sort_by].desc() if sort_order == 'desc' else sortable_fields[sort_by].asc()

    # Base query for products
    query = Product.query.order_by(sort_func)

    # Filter by category if category_id is provided
    if category_id:
        query = query.filter_by(category_id=category_id)

    # Filter by feature_type if it's provided
    if feature_type:
        query = query.filter_by(feature_type=feature_type)

    if gender:
        query = query.filter(Product.gender == gender)

    # Paginate the query
    paginated_products = query.paginate(page=page, per_page=per_page, error_out=False)

    # Build the result list with all product details
    result = []
    for product in paginated_products.items:
        # Fetch all media for the product (multiple media files as an array of URLs)
        media_files = Media.query.filter_by(product_id=product.product_id).order_by(Media.created_at).all()
        media_urls = [media.name for media in media_files] if media_files else []

        # Fetch variants for the product
        variants = Variant.query.filter_by(product_id=product.product_id).all()
        variant_list = []
        for variant in variants:
            # Fetch all media for each variant (multiple media files as an array of URLs)
            variant_media_files = Media.query.filter_by(variant_id=variant.variant_id).order_by(Media.created_at).all()
            variant_media_urls = [media.name for media in variant_media_files] if variant_media_files else []

            variant_dict = {
                column.name: getattr(variant, column.name) for column in variant.__table__.columns
            }
            variant_dict['media'] = variant_media_urls  # Media for each variant as an array

            variant_list.append(variant_dict)

        # Build product dictionary
        product_dict = {
            column.name: getattr(product, column.name) for column in product.__table__.columns
        }

        # Calculate average rating (float with 1 decimal place)
        avg_rating = None
        if product.total_reviews > 0:
            avg_rating = round(product.current_rating_sum / product.total_reviews, 1)

        product_dict['media'] = media_urls  # Media for the product as an array
        product_dict['average_rating'] = avg_rating  # Float rating rounded to 1 decimal
        product_dict['variants'] = variant_list

        result.append(product_dict)

    # Return the paginated response
    return jsonify({
        'products': result,
        'page': paginated_products.page,
        'total_pages': paginated_products.pages,
        'total_products': paginated_products.total,
        'has_next': paginated_products.has_next,
        'has_prev': paginated_products.has_prev
    })


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
    user_id = data.get('user_id')
    if current_user_id != user_id:
        return jsonify({"message": current_user_id}), 401
    else:
        return jsonify({"message": "Authorized"}), 200


@main.route('/orders', methods=['POST'])
def place_order():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    user_id = data.get('user_id')

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

@main.route('/cart/<int:user_id>', methods=['GET'])
def get_cart_items(user_id):
    # Query the cart items for the given user_id
    cart_items = (
        CartItem.query
        .join(Cart, Cart.cart_id == CartItem.cart_id)
        .join(Product, Product.product_id == CartItem.product_id)
        .filter(Cart.user_id == user_id)
        .all()
    )

    # Initialize response variables
    items_data = []
    total_price = 0
    total_items = len(cart_items)

    # Process each cart item
    for item in cart_items:
        product = Product.query.filter_by(product_id=item.product_id).first()

        # Get product variants if applicable
        variants = Variant.query.filter_by(product_id=product.product_id).all()

        # Check if the product has a variant and load the correct media
        if item.variant_id:
            media = Media.query.filter_by(variant_id=item.variant_id).all()
        else:
            media = Media.query.filter_by(product_id=item.product_id).all()

        # Collect media URLs
        media_urls = [m.url for m in media]  # Assuming `url` is a column in Media

        # Calculate subtotal for this item
        subtotal = item.price_at_added * item.quantity
        total_price += subtotal

        # Append item data to response
        items_data.append({
            'cart_item_id': item.cart_item_id,
            'product_id': product.product_id,
            'product_name': product.product_name,
            'quantity': item.quantity,
            'price_at_added': item.price_at_added,
            'subtotal': subtotal,
            'variant_id': item.variant_id,
            'media': media_urls,
            'variants': [{'variant_id': v.variant_id, 'size': v.size, 'color': v.color} for v in variants]
        })

    # Final response with items and cart totals
    return jsonify({
        'cart_items': items_data,
        'total_price': total_price,
        'total_items': total_items
    }), 200


@main.route('/cart/add', methods=['POST'])
def add_product_to_cart():
    user_id = request.json.get('user_id')
    product_id = request.json.get('product_id')
    variant_id = request.json.get('variant_id', None)  # Optional
    quantity = request.json.get('quantity', 1)  # Default is 1

    # Check if user ID and product ID are provided
    if not user_id or not product_id:
        return jsonify({'error': 'user_id and product_id are required'}), 400

    # Fetch or create a new cart for the user
    cart = Cart.query.filter_by(user_id=user_id).first()
    if not cart:
        # If the cart doesn't exist, create a new one
        cart = Cart(user_id=user_id, created_at=datetime.now())
        db.session.add(cart)
        db.session.commit()

    # Check if the product exists
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product does not exist'}), 404

    # Check if the variant exists (if variant_id is provided)
    if variant_id:
        variant = Variant.query.get(variant_id)
        if not variant:
            return jsonify({'error': 'Variant does not exist'}), 404

    # Calculate the subtotal (you can replace this with your actual logic)
    # For simplicity, assume we have a price field in the Product model
    price = product.price  # Assuming variant has a price field
    subtotal = price * quantity

    # Add the product to the cart items (or update if already exists)
    cart_item = CartItem.query.filter_by(cart_id=cart.cart_id, product_id=product_id, variant_id=variant_id).first()
    if cart_item:
        # If the item already exists in the cart, update the quantity and subtotal
        cart_item.quantity += quantity
        cart_item.subtotal += subtotal
    else:
        # If the item does not exist, create a new cart item
        cart_item = CartItem(
            cart_id=cart.cart_id,
            product_id=product_id,
            variant_id=variant_id,
            quantity=quantity,
            subtotal=subtotal
        )
        db.session.add(cart_item)

    try:
        db.session.commit()
        return jsonify({'message': 'Product added to cart successfully'}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Failed to add product to cart'}), 500


@main.route('/add_to_wishlist', methods=['POST'])
def add_to_wishlist():
    user_id = request.json.get('user_id')
    product_id = request.json.get('product_id')
    variant_id = request.json.get('variant_id', None)

    # Check if a saved list exists for the user, create if not
    saved = Saved.query.filter_by(user_id=user_id).first()
    if not saved:
        saved = Saved(user_id=user_id)
        db.session.add(saved)
        db.session.commit()

    # Add item to saved items
    saved_item = SavedItem.query.filter_by(saved_id=saved.saved_id, product_id=product_id, variant_id=variant_id).first()
    if not saved_item:
        saved_item = SavedItem(saved_id=saved.saved_id, product_id=product_id, variant_id=variant_id)
        db.session.add(saved_item)
        db.session.commit()

    return jsonify({'message': 'Item added to wishlist successfully'}), 201