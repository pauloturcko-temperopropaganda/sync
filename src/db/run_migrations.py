import os
import re

from src.db.admin import get_connection


MIGRATIONS_DIR = os.path.join(
    os.path.dirname(__file__),
    "..",
    "migrations",
)

_DOLLAR_TAG_RE = re.compile(r"\$[a-zA-Z_]*\$")


def split_sql_statements(sql_script: str) -> list[str]:
    """Separa um script SQL em statements individuais por ';'.

    Diferente de um split ingênuo, respeita blocos delimitados por
    dollar-quoting (`$$ ... $$` ou `$tag$ ... $tag$`, usados em corpos
    de função PL/pgSQL), strings entre aspas simples e comentários de
    linha (`-- ...`) — um ';' dentro de qualquer um desses contextos
    não separa statements (comentários em português usam ';' como
    pontuação normal, não só o SQL).
    """

    statements = []
    buffer: list[str] = []
    i = 0
    n = len(sql_script)
    dollar_tag = None
    in_single_quote = False
    in_line_comment = False

    while i < n:
        char = sql_script[i]

        if in_line_comment:
            buffer.append(char)
            if char == "\n":
                in_line_comment = False
            i += 1
            continue

        if dollar_tag:
            if sql_script.startswith(dollar_tag, i):
                buffer.append(dollar_tag)
                i += len(dollar_tag)
                dollar_tag = None
                continue
            buffer.append(char)
            i += 1
            continue

        if in_single_quote:
            buffer.append(char)
            if char == "'":
                in_single_quote = False
            i += 1
            continue

        if char == "-" and sql_script.startswith("--", i):
            in_line_comment = True
            buffer.append("--")
            i += 2
            continue

        if char == "'":
            in_single_quote = True
            buffer.append(char)
            i += 1
            continue

        if char == "$":
            match = _DOLLAR_TAG_RE.match(sql_script, i)
            if match:
                dollar_tag = match.group(0)
                buffer.append(dollar_tag)
                i += len(dollar_tag)
                continue

        if char == ";":
            statements.append("".join(buffer))
            buffer = []
            i += 1
            continue

        buffer.append(char)
        i += 1

    tail = "".join(buffer)
    if tail.strip():
        statements.append(tail)

    return [s.strip() for s in statements if s.strip()]


def get_applied_migrations(cursor):
    cursor.execute(
        """
        SELECT COUNT(*) AS table_exists
        FROM information_schema.tables
        WHERE table_schema = current_schema()
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

            for statement in split_sql_statements(sql_script):
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
