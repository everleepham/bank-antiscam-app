from flask import Flask
from app.routes import auth_routes, transactions_routes

def create_app():
    app = Flask(__name__)
    app.secret_key = 'your_secret_key_here'
    
    # Register blueprints
    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(transactions_routes.bp)
    
    return app