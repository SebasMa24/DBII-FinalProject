import os
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

class DBSettings(BaseModel):
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