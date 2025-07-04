from app.db.neo4j import neo4j_driver
from pydantic import BaseModel, Field
from .mongo_model import TransactionStatus

class Neo4jBaseModel:
    driver = neo4j_driver
    
class UserSchema(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    fname: str = Field(..., description="User first name")
    lname: str = Field(..., description="User last name")
    score: int = Field(default=0, description="User score")
    
class TransactionSchema(BaseModel):
    transaction_id: str = Field(..., description="Unique transaction identifier")
    amount: float = Field(..., gt=0, description="Transaction amount")
    status: TransactionStatus = Field(default=TransactionStatus.PENDING)
    timestamp: str = Field(..., description="Transaction timestamp in ISO format")
    
class DeviceSchema(BaseModel):
    device_id: str = Field(..., description="Unique device identifier")
    mac_address: str = Field(..., description="Device MAC address")
    ip_address: str = Field(..., description="Device IP address")

class Neo4jUserModel(Neo4jBaseModel):
    @staticmethod
    def create_constraints(tx):
        query = """
        CREATE CONSTRAINT user_id_unique IF NOT EXISTS
        FOR (u:User)
        REQUIRE u.user_id IS UNIQUE
        """
        tx.run(query)

    def create(self, user: UserSchema):
        with self.driver.session() as session:
            print(f"[DEBUG] Creating user: {user.user_id}")
            return session.execute_write(self._create_user_node, user.dict())

    def read(self, user_id=None):
        with self.driver.session() as session:
            if user_id:
                return session.execute_read(self._get_user_by_id, user_id)
            return session.execute_read(self._get_all_users)

    def update(self, user_id, user: UserSchema):
        with self.driver.session() as session:
            return session.execute_write(self._update_user, user_id, user.dict())

    def delete(self, user_id):
        with self.driver.session() as session:
            return session.execute_write(self._delete_user, user_id)

    @staticmethod
    def _create_user_node(tx, data):
        query = """
        MERGE (u:User {user_id: $user_id})
        ON CREATE SET u.fname = $fname,
                    u.lname = $lname,
                    u.score = $score
        RETURN id(u) AS node_id
        """
        result = tx.run(query, **data)
        return result.single()["node_id"]


    @staticmethod
    def _get_user_by_id(tx, user_id):
        query = """
        MATCH (u:User {user_id: $user_id})
        RETURN u
        """
        result = tx.run(query, user_id=user_id)
        return result.single()["u"] if result.peek() else None

    @staticmethod
    def _get_all_users(tx):
        query = "MATCH (u:User) RETURN u"
        result = tx.run(query)
        return [record["u"] for record in result]

    @staticmethod
    def _update_user(tx, user_id, data):
        query = """
        MATCH (u:User {user_id: $user_id})
        SET u += $data
        RETURN count(u) > 0 AS updated
        """
        result = tx.run(query, user_id=user_id, data=data)
        return result.single()["updated"]

    @staticmethod
    def _delete_user(tx, user_id):
        count_result = tx.run("MATCH (u:User {user_id: $user_id}) RETURN COUNT(u) AS count", user_id=user_id)
        count = count_result.single()["count"]
        if count == 0:
            return False
        tx.run("MATCH (u:User {user_id: $user_id}) DELETE u", user_id=user_id)
        return True


class Neo4jTransactionModel(Neo4jBaseModel):
    @staticmethod
    def create_constraints(tx):
        query = """
        CREATE CONSTRAINT transaction_id_unique IF NOT EXISTS
        FOR (t:Transaction)
        REQUIRE t.transaction_id IS UNIQUE
        """
        tx.run(query)

    
    def create(self, txn: TransactionSchema):
        with self.driver.session() as session:
            print(f"[DEBUG] Creating txn: {txn.transaction_id}")
            return session.execute_write(self._create_transaction_node, txn.dict())
        
    def read(self, transaction_id=None):
        with self.driver.session() as session:
            if transaction_id:
                return session.execute_read(self._get_transaction_by_id, transaction_id)
            return session.execute_read(self._get_all_transactions)
        
    def update(self, transaction_id, txn: TransactionSchema):
        with self.driver.session() as session:
            return session.execute_write(self._update_transaction, transaction_id, txn.dict())
        
    def delete(self, transaction_id):
        with self.driver.session() as session:
            return session.execute_write(self._delete_transaction, transaction_id)
        
        
    @staticmethod
    def _create_transaction_node(tx, data):
        query = """
        MERGE (t:Transaction {transaction_id: $transaction_id})
        ON CREATE SET t.amount = $amount,
                    t.timestamp = $timestamp,
                    t.status = $status
        RETURN id(t) AS node_id
        """
        result = tx.run(query, **data)
        return result.single()["node_id"]

    
    @staticmethod
    def _get_transaction_by_id(tx, transaction_id):
        query = """
        MATCH (t:Transaction {transaction_id: $transaction_id})
        RETURN t
        """
        result = tx.run(query, transaction_id=transaction_id)
        return result.single()["t"] if result.peek() else None
    
    @staticmethod
    def _get_all_transactions(tx):
        query = "MATCH (t:Transaction) RETURN t"
        result = tx.run(query)
        return [record["t"] for record in result]
    
    @staticmethod
    def _update_transaction(tx, transaction_id, data):
        query = """
        MATCH (t:Transaction {transaction_id: $transaction_id})
        SET t += $data
        RETURN count(t) > 0 AS updated
        """
        result = tx.run(query, transaction_id=transaction_id, data=data)
        return result.single()["updated"]
    
    @staticmethod
    def _delete_transaction(tx, transaction_id):
        count_result = tx.run(
            "MATCH (t:Transaction {transaction_id: $transaction_id}) RETURN COUNT(t) AS count",
            transaction_id=transaction_id
        )
        count = count_result.single()["count"]
        if count == 0:
            return False
        tx.run("MATCH (t:Transaction {transaction_id: $transaction_id}) DELETE t", transaction_id=transaction_id)
        return True

    
class Neo4jDeviceModel(Neo4jBaseModel):
    @staticmethod
    def create_constraints(tx):
        query = """
        CREATE CONSTRAINT device_id_unique IF NOT EXISTS
        FOR (d:Device)
        REQUIRE d.device_id IS UNIQUE
        """
        tx.run(query)
        
    def create(self, device: DeviceSchema):
        with self.driver.session() as session:
            return session.execute_write(self._create_device_node, device.dict())
        
    def read(self, device_id=None):
        with self.driver.session() as session:
            if device_id:
                return session.execute_read(self._get_device_by_id, device_id)
            return session.execute_read(self._get_all_devices)
        
    def update(self, device_id, device: DeviceSchema):
        with self.driver.session() as session:
            return session.execute_write(self._update_device, device_id, device.dict())
        
    def delete(self, device_id):
        with self.driver.session() as session:
            return session.execute_write(self._delete_device, device_id)
        
    
    @staticmethod
    def _create_device_node(tx, data):
        query = """
        MERGE (d:Device {device_id: $device_id})
        ON CREATE SET d.mac_address = $mac_address,
                    d.ip_address = $ip_address
        RETURN id(d) AS node_id
        """
        result = tx.run(query, **data)
        return result.single()["node_id"]

    @staticmethod
    def _get_device_by_id(tx, device_id):
        query = """
        MATCH (d:Device {device_id: $device_id})
        RETURN d
        """
        result = tx.run(query, device_id=device_id)
        return result.single()["d"] if result.peek() else None
    
    @staticmethod
    def _get_all_devices(tx):
        query = "MATCH (d:Device) RETURN d"
        result = tx.run(query)
        return [record["d"] for record in result]
    
    @staticmethod
    def _update_device(tx, device_id, data):
        query = """
        MATCH (d:Device {device_id: $device_id})
        SET d += $data
        RETURN count(d) > 0 AS updated
        """
        result = tx.run(query, device_id=device_id, data=data)
        return result.single()["updated"]
    
    @staticmethod
    def _delete_device(tx, device_id):
        count_result = tx.run("MATCH (d:Device {device_id: $device_id}) RETURN COUNT(d) AS count", device_id=device_id)
        count = count_result.single()["count"]
        if count == 0:
            return False
        tx.run("MATCH (d:Device {device_id: $device_id}) DELETE d", device_id=device_id)
        return True
