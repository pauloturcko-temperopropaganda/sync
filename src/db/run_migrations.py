import os

from src.db.admin import get_connection


MIGRATIONS_DIR = os.path.join(
    os.path.dirname(__file__),
    "..",
    "migrations",
)


def get_applied_migrations(cursor):
    cursor.execute(
        """
        SELECT COUNT(*)
        AS table_exists
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
          AND table_name = 'schema_migrations';
        """
    )

    if cursor.fetchone()["table_exists"] == 0:
        return set()

    cursor.execute("SELECT filename FROM schema_migrations;")
    return {row["filename"] for row in cursor.fetchall()}


def run_migrations():
    with get_connection() as conn:
        cursor = conn.cursor()

        applied = get_applied_migrations(cursor)

        files = sorted(
            f for f in os.listdir(MIGRATIONS_DIR)
            if f.endswith(".sql")
        )

        pending = [f for f in files if f not in applied]

        if not pending:
            print("Nenhuma migration pendente.")
            return

        for filename in pending:
            path = os.path.join(MIGRATIONS_DIR, filename)

            print(f"Aplicando {filename}...")

            with open(path, "r", encoding="utf-8") as f:
                sql_script = f.read()

            for statement in sql_script.split(";"):
                statement = statement.strip()

                if statement:
                    cursor.execute(statement)

            cursor.execute(
                """
                INSERT INTO schema_migrations (filename)
                VALUES (%s)
                """,
                (filename,),
            )

            conn.commit()

            print(f"{filename} aplicada com sucesso.")


if __name__ == "__main__":
    run_migrations()