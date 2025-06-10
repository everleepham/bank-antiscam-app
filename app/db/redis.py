# app/db/redis.py
import redis
from app.utils.config import Config

try:
    redis_client = redis.from_url(Config.REDIS_URI)
    redis_client.ping()
    print("Redis connection established.")
except redis.RedisError as e:
    print("Redis connection failed:", e)