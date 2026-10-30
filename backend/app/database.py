import os

from sqlalchemy import create_engine

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://apex:apex_dev_password@localhost:5434/apex",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
