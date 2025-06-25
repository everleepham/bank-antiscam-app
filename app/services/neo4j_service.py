from app.db.neo4j import neo4j_driver
from app.models.neo4j_model import (
    Neo4jUserModel,
    Neo4jTransactionModel,
    Neo4jDeviceModel,
)


class Neo4jService:
    driver = neo4j_driver

    @staticmethod
    def setup_constraints():
        with Neo4jService.driver.session() as session:
            session.execute_write(Neo4jUserModel.create_constraints)
            session.execute_write(Neo4jTransactionModel.create_constraints)
            session.execute_write(Neo4jDeviceModel.create_constraints)

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
        MATCH (user:User {user_id: $user_id})-[:MADE]->(txn:Transaction)
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
        WITH sent_to, collect(DISTINCT other2) AS received_from
        WITH sent_to + received_from AS all_users
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
        """
        Detecys a circular transaction paths starting and ending at the same user,
        alternating between User and Transaction nodes. Filters cycles whose total
        transaction time is within $max_diff_minutes minutes to detect suspicious
        money laundering or fraud behavior efficiently.
        """

        max_diff_minutes = tx_data.get("max_diff_minutes", 30)
        query = """
        MATCH path = (start:User {user_id: $user_id})-[:MADE|TO*2..20]->(start)
        WITH path, nodes(path) AS path_nodes
        WHERE ALL(i IN range(0, size(path_nodes) - 1)
            WHERE (i % 2 = 0 AND "User" IN labels(path_nodes[i]))
            OR (i % 2 = 1 AND "Transaction" IN labels(path_nodes[i]))
        )
        WITH path_nodes, [n IN path_nodes WHERE "Transaction" IN labels(n)] AS txns
        WITH path_nodes, txns,
            reduce(minTime = datetime("9999-12-31T23:59:59"), t IN txns | 
                CASE WHEN t.timestamp < minTime THEN t.timestamp ELSE minTime END) AS earliest,
            reduce(maxTime = datetime("0000-01-01T00:00:00"), t IN txns | 
                CASE WHEN t.timestamp > maxTime THEN t.timestamp ELSE maxTime END) AS latest
        WHERE duration.between(earliest, latest).minutes < $max_diff_minutes
        RETURN 
            [n IN path_nodes | CASE WHEN "Transaction" IN labels(n) THEN n.transaction_id ELSE n.user_id END] AS path_ids,
            duration.between(earliest, latest).minutes AS time_diff,
            size(txns) AS num_transactions
        LIMIT 1
        """
        with self.driver.session() as session:
            result = session.run(
                query, user_id=tx_data["user_id"], max_diff_minutes=max_diff_minutes
            )
            record = result.single()
            if record:
                return {
                    "path_ids": record["path_ids"],
                    "time_diff": record["time_diff"],
                    "num_transactions": record["num_transactions"],
                }
        return None
