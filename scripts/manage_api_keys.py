"""
Issue, list and revoke API keys for the external REST API (/api/v1).

    python scripts/manage_api_keys.py create "Partner Team"
    python scripts/manage_api_keys.py list
    python scripts/manage_api_keys.py revoke 3

On the Docker server, run it inside the web container:

    docker compose exec web python scripts/manage_api_keys.py create "Partner Team"

The plain key is printed ONCE by `create` — only its hash is stored, so it
can't be shown again. If a key is lost or leaked, revoke it and issue a new one.
The api_keys table is created automatically the first time this runs.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api.auth import generate_key, hash_key
from app.database import SessionLocal, engine
from app.models import ApiKey


def create(db, name: str):
    plain_key = generate_key()
    api_key = ApiKey(name=name.strip(), key_prefix=plain_key[:12], key_hash=hash_key(plain_key))
    db.add(api_key)
    db.commit()
    print(f"Created API key #{api_key.id} for '{api_key.name}':\n")
    print(f"    {plain_key}\n")
    print("Copy it now and send it to the client securely — it will not be shown again.")


def list_keys(db):
    keys = db.query(ApiKey).order_by(ApiKey.id.asc()).all()
    if not keys:
        print("No API keys yet.")
        return
    print(f"{'ID':>4}  {'STATUS':8}  {'PREFIX':14}  {'CREATED':19}  {'LAST USED':19}  NAME")
    for k in keys:
        created = k.created_at.strftime("%Y-%m-%d %H:%M:%S") if k.created_at else "-"
        last_used = k.last_used_at.strftime("%Y-%m-%d %H:%M:%S") if k.last_used_at else "never"
        state = "active" if k.is_active else "revoked"
        print(f"{k.id:>4}  {state:8}  {k.key_prefix + '...':14}  {created:19}  {last_used:19}  {k.name}")


def revoke(db, key_id: int):
    api_key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    if not api_key:
        sys.exit(f"No API key with id {key_id}.")
    api_key.is_active = False
    db.commit()
    print(f"Revoked API key #{api_key.id} ('{api_key.name}'). It stops working immediately.")


def main():
    parser = argparse.ArgumentParser(description="Manage REST API keys.")
    sub = parser.add_subparsers(dest="command", required=True)
    p_create = sub.add_parser("create", help="Issue a new key")
    p_create.add_argument("name", help="Who the key is for, e.g. 'Partner Team'")
    sub.add_parser("list", help="List all keys")
    p_revoke = sub.add_parser("revoke", help="Disable a key")
    p_revoke.add_argument("id", type=int)
    args = parser.parse_args()

    ApiKey.__table__.create(bind=engine, checkfirst=True)

    db = SessionLocal()
    try:
        if args.command == "create":
            create(db, args.name)
        elif args.command == "list":
            list_keys(db)
        elif args.command == "revoke":
            revoke(db, args.id)
    finally:
        db.close()


if __name__ == "__main__":
    main()
