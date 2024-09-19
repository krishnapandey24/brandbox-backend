import mimetypes
import os

from MySQLdb import IntegrityError
from flask import Blueprint
from flask import current_app
from flask import request, jsonify
from werkzeug.utils import secure_filename

from . import Config
from .models import Product, db, Media, Category, Variant

admin = Blueprint('admin', __name__)


@admin.route('/admin')
def home():
    return "admin"


@admin.route('/add_product', methods=['POST'])
def add_product():
    data = request.form.to_dict()

    try:
        # Add the product
        product = Product(
            product_name=data['product_name'],
            description=data.get('description'),
            price=data['price'],
            fake_price=data.get('fake_price', 0.0),
            stock_quantity=data['stock_quantity'],
            sales=data.get('sales', 0),
            current_rating_sum=data.get('current_rating_sum', 0.0),
            total_reviews=data.get('total_reviews', 0),
            feature_type=data.get('feature_type', 'basic'),
            gender=data.get('gender', 'both'),
            category_id=data['category_id']
        )
        db.session.add(product)
        db.session.commit()

        # Handle media for the product
        media_files = request.files.getlist('media')
        for media_file in media_files:
            filename = secure_filename(media_file.filename)
            filepath = os.path.join(current_app.config['MEDIA_FOLDER'], filename)
            media_file.save(filepath)

            media = Media(
                product_id=product.product_id,
                variant_id=None,  # Not applicable
                media_type=get_media_type(media_file.filename),
                name=filename
            )
            db.session.add(media)

        db.session.commit()

        # Add variants if any
        if 'variants' in data:
            for v in data['variants']:
                variant = Variant(
                    size=v.get('size'),
                    color_id=v.get('color_id'),
                    stock_quantity=v['stock_quantity'],
                    product_id=product.product_id
                )
                db.session.add(variant)
                db.session.commit()

                # Handle media for the variant
                variant_media_files = request.files.getlist(f'variant_{variant.variant_id}_media')
                for media_file in variant_media_files:
                    filename = secure_filename(media_file.filename)
                    filepath = os.path.join(current_app.config['MEDIA_FOLDER'], filename)
                    media_file.save(filepath)

                    media = Media(
                        product_id=None,  # Not applicable
                        variant_id=variant.variant_id,
                        media_type=get_media_type(media_file.filename),
                        name=filename
                    )
                    db.session.add(media)

                db.session.commit()

        return jsonify({'message': 'Product added successfully'}), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Integrity Error occurred'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin.route('/products/<int:product_id>/media', methods=['POST'])
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
    is_image = file.content_type.startswith('image/')
    is_video = file.content_type.startswith('video/')
    if file and (is_image or is_video):
        # Save the file
        filename = secure_filename(file.filename)
        file_path = os.path.join(Config.MEDIA_FOLDER, filename)
        file.save(file_path)

        # Create new media record
        new_media = Media(
            product_id=product_id,
            media_type="image" if is_image else "video",
            name=filename  # Save the path or URL of the file
        )

        # Add and commit to the database
        db.session.add(new_media)
        db.session.commit()

        return jsonify({"message": "Media added successfully", "media_id": new_media.id}), 201

    return jsonify({"message": "Invalid file type"}), 400


def get_media_type(filename):
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type:
        if mime_type.startswith('image'):
            return 'image'
        elif mime_type.startswith('video'):
            return 'video'
    return None  # Handle u


@admin.route('/category', methods=['POST'])
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
