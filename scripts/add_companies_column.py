"""
One-off migration: add the `companies` column to the users table.

SQLAlchemy's create_all() only creates missing tables, it never alters an
existing one, so an already-deployed database needs this column added by hand.
Safe to run more than once.

    python scripts/add_companies_column.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app.database import engine


def main():
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS companies TEXT"))
    print("OK — users.companies column is present.")


if __name__ == "__main__":
    main()
