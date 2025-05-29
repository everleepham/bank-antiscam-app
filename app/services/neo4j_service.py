from neo4j import GraphDatabase
from app.utils.config import Config

class Neo4jService:
    
    def __init__(self):
        self.driver = GraphDatabase.driver(
            Config.NEO4J_URI,
            auth=(Config.NEO4J_USER, Config.NEO4J_PASSWORD)
        )
        
    def connect_user_transaction_user(self, tx_data):
        """
        tx_data = {
            "sender_id": "user123",
            "receiver_id": "user456",
            "transaction_id": "txn789"
        }
        """
        query = """
        MATCH (sender:User {user_id: $sender_id})
        MATCH (receiver:User {user_id: $receiver_id})
        MATCH (txn:Transaction {transaction_id: $transaction_id})
        MERGE (sender)-[:MADE]->(txn)
        MERGE (txn)-[:TO]->(receiver)
        RETURN sender, txn, receiver
        """
        
        with self.driver.session() as session:
            result = session.run(query, **tx_data)
            return result.single()
        

    def connect_user_device(self, tx_data):
        query = """
        MATCH (user:User {user_id: $user_id})
        MATCH (device:Device {device_id: $device_id})
        MERGE (user)-[:USES]->(device)
        RETURN user, device
        """
        
        with self.driver.session() as session:
            result = session.run(query, **tx_data)
            return result.single()
    
    def get_user_transactions_connections(self, tx_data):
        query = """
        MATCH (user:User {user_id: $user_id})-[:MADE*]->(txn:Transaction)
        RETURN txn
        """
        
        with self.driver.session() as session:
            result = session.run(query, **tx_data)
            return [record["txn"] for record in result]
    
    def get_user_user_connections(self, tx_data):
        query = """
        MATCH (sender:User)-[:MADE]->(txn:Transaction)<-[:TO]-(receiver:User)
        WHERE sender.user_id = $sender_id
        RETURN DISTINCT receiver
        """
        
        with self.driver.session() as session:
            result = session.run(query, **tx_data)
            return result.data()
    
    def get_user_device_connections(self, tx_data):
        query = """
        MATCH (user:User {user_id: $user_id})-[:USES]->(device:Device)
        RETURN collect(device) as devices, count(device) as total_devices
        """
        
        with self.driver.session() as session:
            result = session.run(query, **tx_data)
            return result.data()
    
