from fastapi import HTTPException
from flask import Blueprint, request, jsonify
from app.services.redis_service import RedisTrustScoreService
from app.models.mongo_model import MongoUserModel, DeviceLogModel, User, DeviceLog
from app.services.mongo_service import MongoService
from app.models.neo4j_model import Neo4jUserModel, UserSchema
from app.services.mongo_service import MongoService
from app.services.trust_service import enforce_trust_policy
from app.services.score_service import get_score, get_flag_and_warning
from app.utils.trust_score import SCORE
from flask import request, jsonify, Blueprint
import hashlib


user_bp = Blueprint('users', __name__)

redis = RedisTrustScoreService()
mongo = MongoService()
node = Neo4jUserModel()


def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password_hash, provided_password):
    return stored_password_hash == hash_password(provided_password)


@user_bp.route('/register', methods=['POST'])
def register():
    user_data = User(**request.json)
    user_data.password = hash_password(user_data.password)

    mongo = MongoUserModel()
    mongo.create(user_data)

    # Neo4j
    user_node = UserSchema(
        user_id=user_data.user_id,
        fname=user_data.fname,
        lname=user_data.lname,
        score=user_data.score,
    )
    Neo4jUserModel().create(user_node)
    
    redis.set_score(user_data.user_id, user_data.score) 

    return jsonify({
        "message": "User registered successfully",
        "fname": user_data.fname,
        "lname": user_data.lname,
        "email": user_data.email,
        "score": user_data.score}), 201


@user_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    device_log = data.get("device_log")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = MongoUserModel().collection.find_one({"email": email})
    if not user or not verify_password(user["password"], password):
        return jsonify({"error": "Invalid credentials"}), 401

    user_id = user["user_id"]
    score = get_score(user_id) #get score from redis or mongo
    # if no score in redis, fetch from mongo and set in redis
    flag, warning = get_flag_and_warning(score)

    if score is not None:
        try:
            enforce_trust_policy(user_id, action="login", score=score)
        except HTTPException as e:
            return jsonify({"error": str(e)})

    if device_log:
        device_log["user_id"] = user_id
        try:
            DeviceLogModel().create(DeviceLog(**device_log))
        except Exception as e:
            return jsonify({"error": "Failed to log device information", "details": str(e)}), 500
        
    return jsonify({
        "message": "Login successful",
        "user_email": email,
        "score": score,
        "flag": flag,
        "warning": warning
    }), 200
    

@user_bp.route('/score/{user_id}', methods=['GET'])
def get_user_score(user_id: str):
    new_score = get_score(user_id)
    if new_score is None:
        raise HTTPException(status_code=404, detail="User not found")
    for score in SCORE:
        if score["min"] <= new_score <= score["max"]:
            return {
                "email": user_id, 
                "score": new_score, 
                "flag": score["flag"], 
                "message": score["warning"]
                }
    return None
    


