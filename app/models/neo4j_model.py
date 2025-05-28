from neo4j import GraphDatabase
from app.utils.config import Config

class Neo4jUserModel:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            Config.NEO4J_URI,
            auth=(Config.NEO4J_USER, Config.NEO4J_PASSWORD)
        )

    def create(self, data):
        with self.driver.session() as session:
            return session.execute_write(self._create_user_node, data)

    def read(self, user_id=None):
        with self.driver.session() as session:
            if user_id:
                return session.execute_read(self._get_user_by_id, user_id)
            return session.execute_read(self._get_all_users)

    def update(self, user_id, data):
        with self.driver.session() as session:
            return session.execute_write(self._update_user, user_id, data)

    def delete(self, user_id):
        with self.driver.session() as session:
            return session.execute_write(self._delete_user, user_id)

    @staticmethod
    def _create_user_node(tx, data):
        query = """
        CREATE (u:User {
            user_id: $user_id,
            fname: $fname,
            lname: $lname,
            score: $score
        })
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
        query = """
        MATCH (u:User {user_id: $user_id})
        DELETE u
        RETURN count(u) > 0 AS deleted
        """
        result = tx.run(query, user_id=user_id)
        return result.single()["deleted"]


class Neo4jTransactionModel:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            Config.NEO4J_URI,
            auth=(Config.NEO4J_USER, Config.NEO4J_PASSWORD)
        )
        
    def create(self, data):
        with self.driver.session() as session:
            return session.execute_write(self._create_transaction_node, data)
        
    def read(self, transaction_id=None):
        with self.driver.session() as session:
            if transaction_id:
                return session.execute_read(self._get_transaction_by_id, transaction_id)
            return session.execute_read(self._get_all_transactions)
        
    def update(self, transaction_id, data):
        with self.driver.session() as session:
            return session.execute_write(self._update_transaction, transaction_id, data)
        
    def delete(self, transaction_id):
        with self.driver.session() as session:
            return session.execute_write(self._delete_transaction, transaction_id)
        
        
    @staticmethod
    def _create_transaction_node(tx, data):
        query = """
        CREATE (t:Transaction {
            transaction_id: $transaction_id,
            amount: $amount,
            timestamp: $timestamp,
            status: $status
        })
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
        query = """
        MATCH (t:Transaction {transaction_id: $transaction_id})
        DELETE t
        RETURN count(t) > 0 AS deleted
        """
        result = tx.run(query, transaction_id=transaction_id)
        return result.single()["deleted"]
    
    
class Neo4jDeviceModel:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            Config.NEO4J_URI,
            auth=(Config.NEO4J_USER, Config.NEO4J_PASSWORD)
        )
        
    def create(self, data):
        with self.driver.session() as session:
            return session.execute_write(self._create_device_node, data)
        
    def read(self, device_id=None):
        with self.driver.session() as session:
            if device_id:
                return session.execute_read(self._get_device_by_id, device_id)
            return session.execute_read(self._get_all_devices)
        
    def update(self, device_id, data):
        with self.driver.session() as session:
            return session.execute_write(self._update_device, device_id, data)
        
    def delete(self, device_id):
        with self.driver.session() as session:
            return session.execute_write(self._delete_device, device_id)
        
    @staticmethod
    def _create_device_node(tx, data):
        query = """
        CREATE (d:Device {
            device_id: $device_id,
            mac_address: $mac_address,
            ip_address: $ip_address,
            location: $location
        })
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
        query = """
        MATCH (d:Device {device_id: $device_id})
        DELETE d
        RETURN count(d) > 0 AS deleted
        """
        result = tx.run(query, device_id=device_id)
        return result.single()["deleted"]