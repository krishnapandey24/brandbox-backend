from flask import Blueprint, request, jsonify
from .models import Product, db, Media

products_bp = Blueprint('products', __name__)
media_bp = Blueprint('media', __name__)
main = Blueprint('main', __name__)



