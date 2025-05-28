from app.models.mongo_model import User, Transaction, DeviceLog
from app.services.base_service import BaseService

class MongoService(BaseService):
    def __init__(self):
        self.user_model = User()
        self.transaction_model = Transaction()
        self.device_log_model = DeviceLog()
    
    # User
    def create_user(self, data):
        return self.user_model.create(data)
    
    def get_user_by_id(self, user_id):
        return self.user_model.read(user_id)
    
    # Transactions
    def create_transaction(self, data):
        return self.transaction_model.create(data)
    
    def get_transaction_by_id(self, transaction_id):
        return self.transaction_model.read(transaction_id)
    
    # Device Logs
    def log_device(self, data):
        return self.device_log_model.create(data)

    def get_device_log_by_id(self, device_id):
        return self.device_log_model.read(device_id)
    