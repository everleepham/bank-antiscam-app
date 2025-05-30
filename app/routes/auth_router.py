from fastapi import APIRouter, HTTPException
from app.services.redis_service import RedisService
from app.models.mongo_model import MongoUserModel, DeviceLogModel
from app.models.neo4j_model import Neo4jUserModel
from app.services.mongo_service import MongoService
from app.services.trust_service import enforce_trust_policy

router = APIRouter()
redis = RedisService()

@router.post("/register")
def register(user_data: dict):
    MongoService().create_user(user_data)
    user_node = Neo4jUserModel()
    user_node.create_node(user_data)
    
    return {"message": "User registered"}

@router.post("/login")
def login(credentials: dict, device_log: dict = None):
    user = MongoUserModel().login(credentials['email'], credentials['password'])
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_id = user["user_id"]

    score = redis.get_score(user_id)
    enforce_trust_policy(user_id, action="login")
    score = redis.get_score(user_id)

    
    DeviceLogModel().create(device_log)
    return {"message": "Login successful", "trust_score": score}


