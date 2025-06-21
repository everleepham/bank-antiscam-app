# Export routes for easier imports
from .transactions_routes import txn_bp as transactions_bp
from .auth_routes import user_bp as auth_bp

__all__ = ['transactions_bp', 'auth_bp']