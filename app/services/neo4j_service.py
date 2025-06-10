from app.db.neo4j import neo4j_driver

class Neo4jService:
    driver = neo4j_driver
        
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
        MATCH (u:User {user_id: $user_id})
        MATCH (u)-[:MADE]->(:Transaction)-[:TO]->(other:User)
        WITH collect(DISTINCT other) AS sent_to
        MATCH (other2:User)-[:MADE]->(:Transaction)-[:TO]->(u)
        WITH sent_to + collect(DISTINCT other2) AS all_users
        UNWIND all_users AS connected_user
        RETURN DISTINCT connected_user.user_id AS receiver_id, connected_user.score AS score
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
        

    def detect_circular_transaction(self, tx_data):
        query = """
        MATCH path = (u:User {user_id: $user_id})-[:MADE*1..$max_depth]->(txn:Transaction)-[:TO]->(receiver:User)
        WHERE receiver.user_id = $user_id
        RETURN length(path) AS cycle_length, nodes(path) AS path_nodes
        LIMIT 1
        """
        with self.driver.session() as session:
            result = session.run(query, user_id=tx_data["user_id"], max_depth=tx_data.get("max_depth", 4))
            return result.single()

        
