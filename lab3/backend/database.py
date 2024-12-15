import psycopg2
from psycopg2 import OperationalError
import os


DB_HOST = 'db'
DB_NAME = 'finance_db'
DB_USER = 'user'
DB_PASSWORD = 'password'

def get_db_connection():
    """Создает и возвращает соединение с базой данных."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=5432
        )
        return conn
    except OperationalError as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return None

def create_user(username, password):
    """Регистрирует нового пользователя в базе данных."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id;", (username, password))
        user_id = cursor.fetchone()[0]
        conn.commit()
        return user_id
    except psycopg2.IntegrityError as e:
        conn.rollback()
        if 'unique_username' in str(e):
            raise ValueError("Логин уже занят. Выберите другой.")
        else:
            raise e
    finally:
        cursor.close()
        conn.close()

def authenticate_user(username, password):
    """Проверяет пользователя и его пароль."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = %s AND password = %s;", (username, password))
    user_id = cursor.fetchone()
    cursor.close()
    conn.close()
    return user_id[0] if user_id else None

def add_transaction(user_id, transaction_type, category, amount):
    """Добавляет транзакцию в базу данных."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO transactions (user_id, type, category, amount) VALUES (%s, %s, %s, %s) RETURNING id;",
                   (user_id, transaction_type, category, amount))
    transaction_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return transaction_id

def get_transactions(user_id, transaction_type):
    """Получает список транзакций для пользователя."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, category, amount, created_at FROM transactions WHERE user_id = %s AND type = %s;",
        (user_id, transaction_type)
    )
    transactions = cursor.fetchall()
    cursor.close()
    conn.close()
    return [{'id': tx[0], 'category': tx[1], 'amount': tx[2], 'created_at': tx[3]} for tx in transactions]

def delete_transaction(transaction_id):
    """Удаляет транзакцию из базы данных."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = %s;", (transaction_id,))
    conn.commit()
    cursor.close()
    conn.close()

def delete_user(user_id):
    """Удаляет пользователя и его данные из базы."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM transactions WHERE user_id = %s;", (user_id,))
        cursor.execute("DELETE FROM users WHERE id = %s;", (user_id,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
