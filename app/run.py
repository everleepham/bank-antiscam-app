import logging
from flask import Flask, request, jsonify
from pydantic import ValidationError
from .routes.transactions_routes import txn_bp
from .routes.auth_routes import user_bp
from werkzeug.exceptions import HTTPException



# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)

# Force stdout to be unbuffered
import sys
sys.stdout.reconfigure(line_buffering=True)


app.register_blueprint(user_bp, url_prefix='/')
app.register_blueprint(txn_bp, url_prefix='/transactions')


# convert HTML error responses to JSON
@app.errorhandler(HTTPException)
def handle_http_exception(e):
    response = e.get_response()
    response.data = jsonify({
        "error": e.description
    }).data
    response.content_type = "application/json"
    return response


@app.route("/health")
def health():
    return {"status": "UP"}

def run_app():
    """Entry point for the application script"""
    # Initialize the database before starting the app
    app.run(host="0.0.0.0", port=5050, debug=True)

if __name__ == "__main__":
    run_app()