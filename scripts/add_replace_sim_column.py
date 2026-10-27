"""
One-off migration: add the `replace_sim` checklist column to the jobs table.

SQLAlchemy's create_all() only creates missing tables, it never alters an
existing one, so an already-deployed database needs this column added by hand.
Existing rows get FALSE. Safe to run more than once.

    python scripts/add_replace_sim_column.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app.database import engine


def main():
    with engine.begin() as conn:
        conn.execute(text(
            "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS "
            "replace_sim BOOLEAN NOT NULL DEFAULT FALSE"
        ))
    print("OK — jobs.replace_sim column is present.")


if __name__ == "__main__":
    main()
