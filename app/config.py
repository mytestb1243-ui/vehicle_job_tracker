import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://user:password@localhost:5432/vehiclejobtracker_db"
    )
    SECRET_KEY: str = os.getenv("SECRET_KEY", "insecure-dev-secret-change-me")
    SESSION_MAX_AGE: int = int(os.getenv("SESSION_MAX_AGE", "28800"))

    APP_NAME: str = os.getenv("APP_NAME", "Vehicle Job Tracker")

    DEFAULT_ADMIN_USERNAME: str = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
    DEFAULT_ADMIN_PASSWORD: str = os.getenv("DEFAULT_ADMIN_PASSWORD", "change-this-password")
    DEFAULT_ADMIN_FULLNAME: str = os.getenv(
        "DEFAULT_ADMIN_FULLNAME", "System Administrator"
    )


settings = Settings()
