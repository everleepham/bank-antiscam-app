import redis
from typing import Optional
from app.utils.config import Config

class RedisTrustScoreModel:
    def __init__(self):
        self.redis = redis.from_url(Config.REDIS_URI)
    
    def get(self, key: str) -> Optional[str]:
        return self.redis.get(key)

    def set(self, key: str, value: str, expire_seconds: int = 3600) -> bool:
        return self.redis.set(key, value, ex=expire_seconds)

    def exists(self, key: str) -> bool:
        return self.redis.exists(key) == 1
