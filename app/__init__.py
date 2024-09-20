from flask import Flask
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from .config import Config
from .app_routes import main
from .admin_routes import admin

# Initialize database
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    JWTManager(app)



    app.register_blueprint(main)
    app.register_blueprint(admin)

    # Create tables within the application context
    # with app.app_context():
    #     db.create_all()

    return app
