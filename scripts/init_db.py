"""
Run this once before starting the app for the first time:

    python scripts/init_db.py

Creates all tables (if not already present) and seeds a default
Super Admin account using values from your .env file.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, engine, SessionLocal
from app.models import User
from app.choices import ROLE_SUPER_ADMIN
from app.security import hash_password
from app.config import settings


def main():
    print("Creating tables (if not already present)...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        existing_admin = (
            db.query(User)
            .filter(User.username == settings.DEFAULT_ADMIN_USERNAME.lower())
            .first()
        )
        if existing_admin:
            print(
                f"Admin user '{settings.DEFAULT_ADMIN_USERNAME}' already exists. "
                "Skipping seed."
            )
        else:
            admin = User(
                username=settings.DEFAULT_ADMIN_USERNAME.lower(),
                full_name=settings.DEFAULT_ADMIN_FULLNAME,
                password_hash=hash_password(settings.DEFAULT_ADMIN_PASSWORD),
                role=ROLE_SUPER_ADMIN,
                is_active=True,
            )
            db.add(admin)
            db.commit()
            print(
                f"Created default Super Admin user -> username: "
                f"'{settings.DEFAULT_ADMIN_USERNAME}'  password: "
                f"'{settings.DEFAULT_ADMIN_PASSWORD}'"
            )
            print("IMPORTANT: log in and change this password immediately.")
    finally:
        db.close()

    print("Database ready.")


if __name__ == "__main__":
    main()
