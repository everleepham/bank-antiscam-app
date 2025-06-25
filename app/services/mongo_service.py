from app.models.mongo_model import MongoUserModel, MongoTransactionModel, DeviceLogModel, User, Transaction, DeviceLog, TransactionStatus

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
        """
        Filters the documents in the collection to include only those 
        where the device_id field matches the provided device_id, The second stage,
        reshapes the documents by including only the user_id field and excluding the 
        _id field. This ensures that the output contains only the relevant user IDs.
        """
    
        pipeline = [
            {"$match": {"device_id": device_id}},
            {"$project": {"user_id": 1, "_id": 0}}
        ]
        
        res = list(self.device_log_model.collection.aggregate(pipeline))

        return list({doc["user_id"] for doc in res})

    
    def get_score(self, user_id):
        user = self.user_model.read(user_id)
        if user:
            return user["score"]
        return None
    
    def update_score(self, user_id, score=100):
        user = self.user_model.read(user_id)
        if user:
            user["score"] = score
            user_obj = User(**user)
            return self.user_model.update(user_id, user_obj)
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

    def verify_transaction(self, transaction_id):
        result = self.transaction_model.collection.update_one(
            {"transaction_id": transaction_id},
            {"$set": {"status": TransactionStatus.VERIFIED.value}}
        )
        return result.modified_count == 1
    
    # Device Logs
    def log_device(self, device_log: DeviceLog):
        return self.device_log_model.create(device_log)

    def get_device_log_by_id(self, device_id):
        return self.device_log_model.read(device_id)
    
    def get_devices_by_user(self, user_id):
        """
        The first stage, filters the documents in the collection to include only 
        those where the user_id field matches the provided user_id. The second stage,
        reshapes the documents by including only the device_id field and excluding the 
        _id field. This ensures that the result contains only the relevant device IDs 
        without unnecessary metadata.
        """
        
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$project": {"device_id": 1, "_id": 0}}
        ]

        res = list(self.device_log_model.collection.aggregate(pipeline))
        
        unique_device_ids = {doc["device_id"] for doc in res}
        return list(unique_device_ids)
