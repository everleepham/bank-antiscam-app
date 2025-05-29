from pymongo import MongoClient
from app.utils.config import Config

client = MongoClient(Config.MONGO_URI)
db = client.get_database() 
