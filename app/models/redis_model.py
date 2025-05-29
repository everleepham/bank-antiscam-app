from typing import Optional
from app.db.redis import redis_client

class RedisTrustScoreModel:
    @staticmethod
    def get(key: str) -> Optional[str]:
        return redis_client.get(key)

    @staticmethod
    def set(key: str, value: str, expire_seconds: int = 3600) -> bool:
        return redis_client.set(key, value, ex=expire_seconds)

    @staticmethod
    def exists(key: str) -> bool:
        return redis_client.exists(key) == 1
