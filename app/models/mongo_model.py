from pydantic import BaseModel, EmailStr, Field
from app.db.mongo import db
from typing import Optional
from datetime import datetime
from enum import Enum

class TransactionStatus(str, Enum):
    VERIFIED = "verified"
    PENDING = "pending"
    SUSPICIOUS = "suspicious"
    
class User(BaseModel):
    user_id: str = Field(..., description="Unique user identifier") # define user_id so we can use it with redis and neo4j
    fname: str = Field(..., description="User first name")
    lname: str = Field(..., description="User last name")
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")
    new_user: bool = Field(default=True, description="Is the user new?")
    score: int = Field(default=0, description="User score")
    
class UserInfo(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    user_fname: str = Field(..., description="User first name")
    user_lname: str = Field(..., description="User last name")

class Transaction(BaseModel):
    transaction_id: str = Field(..., description="Unique transaction identifier")
    sender: UserInfo
    sender_device_id: str = Field(..., description="Unique device identifier")
    recipient: UserInfo
    amount: float = Field(..., gt=0, description="Transaction amount")
    timestamp: datetime = Field(default_factory=datetime.now, description="Transaction timestamp")
    status: TransactionStatus = Field(default=TransactionStatus.PENDING)
    flag_reason: Optional[str] = Field(default=None, description="Reason why transaction is flagged")
    
class DeviceLog(BaseModel):
    device_id: str = Field(..., description="Unique device identifier")
    user_id: str = Field(..., description="User ID")
    mac_address: str = Field(..., description="Device MAC address")
    ip_address: str = Field(..., description="Device IP address")
    timestamp: datetime = Field(default_factory=datetime.now, description="Log timestamp")
    location: str = Field(..., description="Device location")
    
class MongoUserModel:
    def __init__(self):
        self.collection = db.users

    def create(self, user: User):
        user_dict = user.dict()
        try:
            self.collection.insert_one(user_dict)
        except Exception as e:
            raise e
        return user_dict

    def read(self, user_id: str):
        return self.collection.find_one({"user_id": user_id})

class MongoTransactionModel:
    def __init__(self):
        self.collection = db.transactions

    def create(self, transaction: Transaction):
        transaction_dict = transaction.dict()
        try: 
            self.collection.insert_one(transaction_dict)
        except Exception as e:
            raise e
        return transaction_dict

    def read(self, transaction_id: str):
        return self.collection.find_one({"transaction_id": transaction_id})
    
    
class DeviceLogModel:
    def __init__(self):
        self.collection = db.device_logs

    def create(self, device_log: DeviceLog):
        device_log_dict = device_log.dict()
        try:
            self.collection.insert_one(device_log_dict)
        except Exception as e:
            raise e
        return device_log_dict

    def read(self, device_id: str):
        return self.collection.find_one({"device_id": device_id})