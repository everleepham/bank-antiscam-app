from pydantic import BaseModel, EmailStr, Field
from pymongo import ReturnDocument
from app.db.mongo import db
from typing import Optional
from datetime import datetime
from enum import Enum

class TransactionStatus(str, Enum):
    VERIFIED = "verified"
    PENDING = "pending"
    SUSPICIOUS = "suspicious"
    
class User(BaseModel):
    user_id: Optional[str] = Field(None, description="Auto-set incremented user ID")
    fname: str = Field(..., description="User first name")
    lname: str = Field(..., description="User last name")
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")
    new_user: bool = Field(default=True, description="Is the user new?")
    score: int = Field(default=0, description="User score")
    plafond: float = Field(default=1000.0, description="User transaction plafond")
    
class UserInfo(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    user_fname: str = Field(..., description="User first name")
    user_lname: str = Field(..., description="User last name")

class Transaction(BaseModel):
    transaction_id: Optional[str] = Field(None, description="Auto-set incremented transaction ID")
    sender: UserInfo
    sender_device_id: str = Field(..., description="Unique device identifier")
    recipient: UserInfo
    amount: float = Field(..., gt=0, description="Transaction amount")
    timestamp: datetime = Field(default_factory=datetime.now, description="Transaction timestamp")
    status: TransactionStatus = Field(default=TransactionStatus.PENDING)
    flag_reason: Optional[str] = Field(default=None, description="Reason why transaction is flagged")
    
class DeviceLog(BaseModel):
    device_id: Optional[str] = Field(None, description="Auto-set from MAC address")
    user_id: str = Field(..., description="User ID")
    mac_address: str = Field(..., description="Actual device MAC address")
    ip_address: str = Field(..., description="Device IP address")
    timestamp: datetime = Field(default_factory=datetime.now, description="Log timestamp")
    location: str = Field(..., description="Device location")
    
class MongoUserModel:
    def __init__(self):
        self.collection = db.users

    def create(self, user: User):
        if not user.user_id:
            user.user_id = get_next_id("user_id")
        self.collection.insert_one(user.dict())
        return user

    def read(self, user_id: str):
        return self.collection.find_one({"user_id": user_id})

class MongoTransactionModel:
    def __init__(self):
        self.collection = db.transactions

    def create(self, txn: Transaction):
        if not txn.transaction_id:
            txn.transaction_id = get_next_id("transaction_id")

        self.collection.insert_one(txn.dict())
        return txn

    def read(self, transaction_id: str):
        return self.collection.find_one({"transaction_id": transaction_id})
    
class DeviceLogModel:
    def __init__(self):
        self.collection = db.device_logs

    def create(self, device_log: DeviceLog):
        device_log_dict = device_log.dict()
        
        mac = device_log_dict.get("mac_address")
        if mac:
            device_log_dict["device_id"] = mac.upper().replace(":", "")  # normalize MAC
        
        try:
            self.collection.insert_one(device_log_dict)
        except Exception as e:
            raise e
        return device_log_dict

    def read(self, device_id: str):
        device_id = device_id.upper().replace(":", "")
        return self.collection.find_one({"device_id": device_id})
    
def get_next_id(name: str) -> str:
    counter = db.counters.find_one_and_update(
        {"_id": name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    return str(counter["seq"]).zfill(3) 