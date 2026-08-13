from src.ai_tools.db import get_connection


def main() -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 AS test")
            result = cursor.fetchone()

    print("Conexão com o banco funcionando.")
    print(f"Resultado: {result}")


if __name__ == "__main__":
    main()