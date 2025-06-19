import pytest
from app.services.mongo_service import MongoService
from app.services.redis_service import RedisTrustScoreService
from app.services.neo4j_service import Neo4jService

from app.db.mongo import db as test_db
from app.db.redis import redis_client 
from app.db.neo4j import neo4j_driver   


@pytest.fixture(scope="function", autouse=True)
def clean_mongo():
    print("Cleaning MongoDB collections...")
    for col in ["users", "transactions", "device_logs", "counters"]:
        test_db[col].delete_many({})
    yield 
        
@pytest.fixture(scope="function", autouse=True)
def clean_redis():
    print("Cleaning Redis database...")
    redis_client.flushdb()
    yield
    
@pytest.fixture(scope="function", autouse=True)
def clean_neo4j():
    print("Cleaning Neo4j database...")
    driver = neo4j_driver
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    yield
    
    
@pytest.fixture(scope="session", autouse=True)
def setup_neo4j_constraints():
    print("Setting up Neo4j constraints...")
    Neo4jService.setup_constraints()
    yield

        
@pytest.fixture
def redis_service():
    return RedisTrustScoreService(ttl=3600)

@pytest.fixture
def mongo_service():
    return MongoService()

@pytest.fixture
def neo4j_service():
    return Neo4jService()
