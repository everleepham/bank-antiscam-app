from app.models.mongo_model import MongoUserModel, MongoTransactionModel, DeviceLogModel, User, Transaction, DeviceLog

class MongoService:
    def __init__(self):
        self.user_model = MongoUserModel()
        self.transaction_model = MongoTransactionModel()
        self.device_log_model = DeviceLogModel()
    
    # User
    def create_user(self, user: User):
        return self.user_model.create(user)
    
    def get_user_by_id(self, user_id):
        return self.user_model.read(user_id)
    
    def get_users_by_device(self, device_id):
        cursor = self.device_log_model.collection.find(
            {"device_id": device_id},
            {"user_id": 1, "_id": 0}
        )
        return list({doc["user_id"] for doc in cursor})

    def login(self, email, password):
        user = self.user_model.read_by_email(email)
        if user and user.password == password:
            return user
        return None
    
    def get_score(self, user_id):
        user = self.user_model.read(user_id)
        if user:
            return user.score
        return None
    
    def update_score(self, user_id, score=100):
        user = self.user_model.read(user_id)
        if user:
            user.score = score
            return self.user_model.update(user_id, user)
        return None
    
    # Transactions
    def create_transaction(self, txn: Transaction):
        return self.transaction_model.create(txn)
    
    def get_transaction_by_id(self, transaction_id):
        return self.transaction_model.read(transaction_id)
    
    def get_transactions_by_sender(self, user_id):
        return list(self.transaction_model.collection.find({"sender.user_id": user_id}))
    
    def get_transactions_by_recipient(self, user_id):
        return list(self.transaction_model.collection.find({"recipient.user_id": user_id}))
    
    # Device Logs
    def log_device(self, device_log: DeviceLog):
        return self.device_log_model.create(device_log)

    def get_device_log_by_id(self, device_id):
        return self.device_log_model.read(device_id)
    
    def get_devices_by_user(self, user_id):
        cursor = self.device_log_model.collection.find(
            {"user_id": user_id},
            {"device_id": 1, "_id": 0}
        )
        unique_device_ids = {doc["device_id"] for doc in cursor}
        return list(unique_device_ids)
