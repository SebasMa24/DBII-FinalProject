import os
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

class DBSettings(BaseModel):
    """
    Loads and holds environment-based configuration settings for database connections.

    This configuration class leverages Pydantic for data validation and loads values 
    from environment variables using `dotenv`. It supports PostgreSQL, MongoDB, and Redis 
    settings.

    Attributes:
        postgres_host (str): Host address for the PostgreSQL database.
        postgres_port (int): Port number for the PostgreSQL connection.
        postgres_db (str): Name of the PostgreSQL database.
        postgres_user (str): Username for PostgreSQL authentication.
        postgres_password (str): Password for PostgreSQL authentication.
        
        mongo_host (str): Host address for the MongoDB database.
        mongo_port (int): Port number for the MongoDB connection.
        mongo_db (str): Name of the MongoDB database.
        mongo_user (str): Username for MongoDB authentication.
        mongo_password (str): Password for MongoDB authentication.

        redis_host (str): Host address for the Redis server.
        redis_port (int): Port number for the Redis connection.
        redis_db (int): Redis logical database index to use.
    """
    
    # PostgreSQL
    postgres_host: str = os.getenv("POSTGRES_HOST")
    postgres_port: int = os.getenv("POSTGRES_PORT")
    postgres_db: str = os.getenv("POSTGRES_DB")
    postgres_user: str = os.getenv("POSTGRES_USER")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD")
    
    # MongoDB
    mongo_host: str = os.getenv("MONGO_HOST")
    mongo_port: int = int(os.getenv("MONGO_PORT"))
    mongo_db: str = os.getenv("MONGO_DB")
    mongo_user: str = os.getenv("MONGO_USER")
    mongo_password: str = os.getenv("MONGO_PASSWORD")

    
    # Redis
    redis_host: str = os.getenv("REDIS_HOST")
    redis_port: int = os.getenv("REDIS_PORT")
    redis_db: int = os.getenv("REDIS_DB")

db_settings = DBSettings()