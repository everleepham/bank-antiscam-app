from pydantic import BaseModel, EmailStr, Field
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

class Transaction(BaseModel):
    sender_id: str = Field(..., description="Sender user ID")
    sender_device_id: str = Field(..., description="Unique device identifier")
    recipient_id: str = Field(..., description="Receiver user ID")
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
        
        

