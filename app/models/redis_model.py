import redis
from typing import Optional
from app.utils.config import Config

class RedisTrustScoreModel:
    def __init__(self):
        self.redis = redis.from_url(Config.REDIS_URI)
    
    def get_score(self, user_id: str) -> Optional[float]:
        score = self.redis.get(user_id)
        if score is not None:
            try:
                return float(score)
            except ValueError:
                return None
        return None
    
    def set_score(self, user_id: str, score: float, expire_seconds: int = 3600) -> bool: #expire time ~ 1 hour
        return self.redis.set(user_id, str(score), ex=expire_seconds)
    
    def exists(self, user_id: str) -> bool:
        return self.redis.exists(user_id) == 1