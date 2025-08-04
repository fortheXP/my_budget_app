import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()


def get_database_url():
    """Get database URL from environment variables or use default"""

    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    # Build from individual components (for development)
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "budget_db")

    # URL encode password to handle special characters
    if db_password:
        db_password = quote_plus(db_password)

    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


DATABASE_URL = get_database_url()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
