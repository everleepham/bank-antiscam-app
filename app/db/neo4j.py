from neo4j import GraphDatabase
from app.utils.config import Config

neo4j_driver = GraphDatabase.driver(
    Config.NEO4J_URI,
    auth=(Config.NEO4J_USER, Config.NEO4J_PASSWORD)
)