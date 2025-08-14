from flask import Flask
from flask_wtf import CSRFProtect
from datetime import date
from .extensions import cache, db
from .admin_routes import admin_bp
from .main_routes import main_bp

def create_app():
    app = Flask(__name__)
    
    # Config
    app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:subburakesh2255@localhost/sxc"
    app.secret_key = "kajsgf74rhisjbdfs"
    app.config["CACHE_TYPE"] = "SimpleCache"
    app.config["CACHE_DEFAULT_TIMEOUT"] = 300

    # Init extensions
    CSRFProtect(app)
    print("Initializing db with app")
    db.init_app(app)
    cache.init_app(app)

    # Register blueprints
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(main_bp)  # quiz + other public routes

    return app
