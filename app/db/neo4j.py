from neo4j import GraphDatabase
from app.utils.config import Config

try:
    neo4j_driver = GraphDatabase.driver(
        Config.NEO4J_URI,
        auth=(Config.NEO4J_USERNAME, Config.NEO4J_PASSWORD)
    )
    with neo4j_driver.session() as session:
        session.run("RETURN 1")
    print("Neo4j connection established.")
except Exception as e:
    print("Neo4j connection failed:", e)