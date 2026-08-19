#!/usr/bin/env python3
"""
Vehicle Job Tracker — quick database console.

Connects automatically using the credentials below (no prompts).
Type a SQL query, press Enter, see the result. Type 'quit' to exit.

*** IMPORTANT — this file contains a live database password. ***
    - Never commit this file to git.
    - Never share it or paste its contents anywhere.
    - Keep it only on your own machine.
"""

import sys

try:
    import psycopg2
except ImportError:
    print("Missing dependency. Run: pip install psycopg2-binary")
    sys.exit(1)


# -----------------------------------------------------------------------------
# Connection details — edit these if the server, port, database, or
# credentials ever change.
# -----------------------------------------------------------------------------
DB_HOST = "173.249.47.19"
DB_PORT = 5432
DB_NAME = "vehicle_job_tracker"
DB_USER = "vjt_user"
DB_PASSWORD = "LB18BJuSHMCbs5HcvohL"
# -----------------------------------------------------------------------------


HELP_TEXT = """
Special commands:
  \\dt              list all tables
  \\d <table>        describe a table's columns
  \\h                show this help
  quit              exit

Anything else is run as raw SQL. End multi-line statements with a semicolon.
Examples:
  SELECT vehicle_no, company_name, job_date FROM jobs ORDER BY job_date DESC LIMIT 10;
  SELECT username, role, is_active FROM users;
  SELECT COUNT(*) FROM jobs WHERE company_name = 'Unilever Trucks';
"""


def get_connection():
    try:
        return psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=10,
        )
    except psycopg2.OperationalError as e:
        print(f"Could not connect to the database:\n{e}")
        sys.exit(1)


def print_table(columns, rows):
    if not rows:
        print("(0 rows)")
        return

    str_rows = [[("" if v is None else str(v)) for v in row] for row in rows]
    widths = [len(col) for col in columns]
    for row in str_rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(val))
    widths = [min(w, 60) for w in widths]

    def fmt_row(values):
        cells = []
        for val, w in zip(values, widths):
            val = val if len(val) <= w else val[: w - 1] + "…"
            cells.append(val.ljust(w))
        return " | ".join(cells)

    print(fmt_row(columns))
    print("-+-".join("-" * w for w in widths))
    for row in str_rows:
        print(fmt_row(row))
    print(f"\n({len(rows)} row{'s' if len(rows) != 1 else ''})")


def run_query(conn, sql):
    sql_stripped = sql.strip().rstrip(";").strip()
    if not sql_stripped:
        return

    is_write = sql_stripped.upper().split(None, 1)[0] in (
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "CREATE"
    )
    if is_write:
        confirm = input(
            f"This looks like a write/DDL statement ({sql_stripped.split()[0].upper()}). "
            "Type 'yes' to run it: "
        )
        if confirm.strip().lower() != "yes":
            print("Cancelled.")
            return

    try:
        with conn.cursor() as cur:
            cur.execute(sql_stripped)
            if cur.description:
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                print_table(columns, rows)
            else:
                conn.commit()
                print(f"OK. {cur.rowcount} row(s) affected.")
    except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
        print(
            "Error: the connection to the database was lost. "
            "Please restart the script and try again."
        )
        print(f"Details: {e}")
        sys.exit(1)
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        print(f"Error: {e}")


def list_tables(conn):
    run_query(
        conn,
        """
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' ORDER BY table_name;
        """,
    )


def describe_table(conn, table_name):
    run_query(
        conn,
        f"""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = '{table_name}'
        ORDER BY ordinal_position;
        """,
    )


def repl(conn):
    print(f"Connected to {DB_NAME} @ {DB_HOST}. Type \\h for help, 'quit' to exit.\n")
    buffer = ""
    while True:
        try:
            prompt = "vjt-db> " if not buffer else "     -> "
            line = input(prompt)
        except (EOFError, KeyboardInterrupt):
            print()
            break

        stripped = line.strip()

        if not buffer:
            if stripped.lower() in ("quit", "exit", "\\q"):
                break
            if stripped in ("\\h", "\\help", "?"):
                print(HELP_TEXT)
                continue
            if stripped == "\\dt":
                list_tables(conn)
                continue
            if stripped.startswith("\\d "):
                describe_table(conn, stripped[3:].strip())
                continue

        buffer += line + " "
        if stripped.endswith(";"):
            run_query(conn, buffer)
            buffer = ""

    print("Bye.")


def main():
    conn = get_connection()
    try:
        repl(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()