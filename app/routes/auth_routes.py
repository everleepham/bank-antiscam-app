from fastapi import HTTPException
from flask import Blueprint
from app.services.redis_service import RedisTrustScoreService
from app.models.mongo_model import MongoUserModel, DeviceLogModel
from app.services.mongo_service import MongoService
from app.models.neo4j_model import Neo4jUserModel
from app.services.mongo_service import MongoService
from app.services.trust_service import enforce_trust_policy
from app.services.score_service import get_score
from app.utils.trust_score import SCORE

bp = Blueprint('users', __name__, url_prefix='/users')
redis = RedisTrustScoreService()
mongo = MongoService()


@bp.route('/register', methods=['POST'])
def register(user_data: dict):
    mongo.create_user(user_data)
    user_node = Neo4jUserModel()
    user_node.create_node(user_data)
    
    return {"message": "User registered"}

@bp.route('/login', methods=['POST'])
def login(credentials: dict, device_log: dict = None):
    user = MongoUserModel().login(credentials['email'], credentials['password'])
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_id = user["user_id"]
    score = get_score(user_id)
    enforce_trust_policy(user_id, action="login", score=score)

    DeviceLogModel().create(device_log)
    return {"message": "Login successful", "trust_score": score}

@bp.route('/score/{user_id}', methods=['POST'])
def get_user_score(user_id: str):
    new_score = get_score(user_id)
    if new_score is None:
        raise HTTPException(status_code=404, detail="User not found")
    for score in SCORE:
        if score["min"] <= new_score <= score["max"]:
            return {
                "user_id": user_id, 
                "score": new_score, 
                "flag": score["flag"], 
                "message": score["warning"]
                }
    return None
    


