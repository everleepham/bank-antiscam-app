from flask import Flask
from app.routes import auth_routes, transactions_routes

def create_app():
    app = Flask(__name__)
    app.secret_key = 'your_secret_key_here'
    
    # Register blueprints
    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(transactions_routes.bp)
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5080, debug=True)