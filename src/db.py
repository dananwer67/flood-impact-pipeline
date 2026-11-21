import os

from dotenv import load_dotenv
from sqlalchemy import create_engine


def get_engine():
    # Read the settings in .env into this program's environment variables.
    load_dotenv()

    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    database = os.getenv("POSTGRES_DB")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")

    # One line that tells SQLAlchemy what kind of database, which driver,
    # who we are, and where the database lives.
    url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{database}"

    return create_engine(url)
