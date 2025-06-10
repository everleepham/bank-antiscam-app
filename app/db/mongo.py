from pymongo import MongoClient
from app.utils.config import Config

client = MongoClient(Config.MONGO_URI)
db = client.get_database("antiscamdb") 
try:
    client.admin.command('ping')
    print("MongoDB connection established.")
except Exception as e:
    print("MongoDB connection failed:", e)