from sqlalchemy import ForeignKey

from . import db
from datetime import datetime, timezone


# User model
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.Enum('google', 'apple'), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Address model
class Address(db.Model):
    __tablename__ = 'addresses'
    address_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    street_address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)
    is_default = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref=db.backref('addresses', lazy=True))

class Category(db.Model):
    __tablename__ = 'categories'
    category_id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)

    # A single category can have many products
    products = db.relationship('Product', backref='category', lazy=True)

class Product(db.Model):
    __tablename__ = 'products'
    product_id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    fake_price = db.Column(db.Numeric(10, 2), nullable=False)
    stock_quantity = db.Column(db.Integer, nullable=False)
    sales = db.Column(db.Integer, default=0)
    current_rating_sum = db.Column(db.Float, default=0.0)
    total_reviews = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    feature_type = db.Column(db.Enum('top_banner_1', 'top_banner_2', 'top_banner_3', 'top_banner_4', 'top_banner_5', 'on_sale', 'featured', 'basic', name='feature_type_enum'), default='basic')
    gender = db.Column(db.Enum('male', 'female', 'both', name='gender_enum'), default='both')

    # ForeignKey to link Product to a Category
    category_id = db.Column(db.Integer, db.ForeignKey('categories.category_id'), nullable=False)

class Order(db.Model):
    __tablename__ = 'orders'
    order_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_status = db.Column(db.Enum('pending', 'confirmed', 'shipped', 'delivered', 'cancelled'), default='pending')
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('orders', lazy=True))


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    order_item_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_at_purchase = db.Column(db.Numeric(10, 2), nullable=False)

    order = db.relationship('Order', backref=db.backref('order_items', lazy=True))
    product = db.relationship('Product', backref=db.backref('order_items', lazy=True))




class Payment(db.Model):
    __tablename__ = 'payments'
    payment_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.Enum('credit_card', 'debit_card', 'paypal', 'bank_transfer'), nullable=False)
    payment_status = db.Column(db.Enum('pending', 'completed', 'failed'), default='pending')
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)

    order = db.relationship('Order', backref=db.backref('payments', lazy=True))



class Media(db.Model):
    __tablename__ = 'media'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=True)
    variant_id = db.Column(db.Integer, db.ForeignKey('variant.variant_id'), nullable=True)
    media_type = db.Column(db.Enum('image', 'video'), nullable=False)
    name = db.Column(db.String(244), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product', backref=db.backref('product_media', lazy=True))
    variant = db.relationship('Variant', backref='variant_media', lazy=True)


class CartItem(db.Model):
    __tablename__ = 'cart_items'

    cart_item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.cart_id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('variant.variant_id'), nullable=True)  # Nullable for products without variants
    quantity = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=True)  # Can be computed as price * quantity

    # Relationships
    product = db.relationship('Product', backref='cart_items', lazy=True)
    variant = db.relationship('Variant', backref='cart_items', lazy=True)

class Saved(db.Model):
    __tablename__ = 'saved'

    saved_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship with saved_items (one-to-many)
    saved_items = db.relationship('SavedItem', backref='saved', lazy=True)


class SavedItem(db.Model):
    __tablename__ = 'saved_items'

    saved_item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    saved_id = db.Column(db.Integer, db.ForeignKey('saved.saved_id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('variant.variant_id'), nullable=True)  # Nullable for products without variants

    # Relationships
    product = db.relationship('Product', backref='saved_items', lazy=True)
    variant = db.relationship('Variant', backref='saved_items', lazy=True)



class Variant(db.Model):
    __tablename__ = 'variant'

    variant_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    size = db.Column(db.Enum('S', 'M', 'L', 'XL', name='size_enum'), nullable=True)
    color_id = db.Column(db.Integer, db.ForeignKey('colors.color_id'), nullable=True)
    stock_quantity = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False)

    color = db.relationship('Color', backref='variants', lazy=True)
    product = db.relationship('Product', backref=db.backref('variants', lazy=True))
    media = db.relationship('Media', backref='variant_media', lazy=True)


class Cart(db.Model):
    __tablename__ = 'carts'

    cart_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship with cart_items (one-to-many)
    cart_items = db.relationship('CartItem', backref='cart', lazy=True)



class Review(db.Model):
    __tablename__ = 'reviews'

    review_id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # Assuming a 1-5 star rating system
    comment = db.Column(db.Text, nullable=True)  # Optional review comment
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    product = db.relationship('Product', backref=db.backref('reviews', lazy=True))
    user = db.relationship('User', backref=db.backref('reviews', lazy=True))


class Color(db.Model):
    __tablename__ = 'colors'

    color_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    color_name = db.Column(db.String(50), nullable=False)
    color_code = db.Column(db.String(7), nullable=False)  # e.g., '#FF0000'

    def __repr__(self):
        return f'<Color {self.color_name} ({self.color_code})>'
