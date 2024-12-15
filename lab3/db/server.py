import os
import json
import psycopg2
import pika

# Конфигурация
DB_HOST = os.getenv("POSTGRES_HOST", "db")
DB_NAME = os.getenv("POSTGRES_DB", "finance_db")
DB_USER = os.getenv("POSTGRES_USER", "user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
#RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_HOST = 'rabbitmq'  # имя хоста, на котором работает RabbitMQ в Docker-сети
QUEUE_NAME = 'test_queue'   # имя очереди, в которую отправляются сообщения

print(f"Attempting to connect to RabbitMQ at {RABBITMQ_HOST}...")

connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
print("Connection to RabbitMQ established.")

# Подключение к базе данных
def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )

# Обработка запросов
def handle_request(ch, method, properties, body):
    response = {}
    try:
        request = json.loads(body)
        command = request.get("command")
        conn = get_db_connection()
        cursor = conn.cursor()

        if command == "register":
            username = request["username"]
            password = request["password"]
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id;",
                (username, password),
            )
            user_id = cursor.fetchone()[0]
            response = {"status": "success", "user_id": user_id}
        elif command == "login":
            username = request["username"]
            password = request["password"]
            cursor.execute(
                "SELECT id FROM users WHERE username = %s AND password = %s;",
                (username, password),
            )
            user = cursor.fetchone()
            if user:
                response = {"status": "success", "user_id": user[0]}
            else:
                response = {"status": "error", "error": "Invalid credentials"}
        elif command == "add_transaction":
            user_id = request["user_id"]
            transaction_type = request["type"]
            category = request["category"]
            amount = request["amount"]
            cursor.execute(
                """
                INSERT INTO transactions (user_id, type, category, amount)
                VALUES (%s, %s, %s, %s);
                """,
                (user_id, transaction_type, category, amount),
            )
            response = {"status": "success"}
        elif command == "get_transactions":
            user_id = request["user_id"]
            transaction_type = request["type"]
            cursor.execute(
                """
                SELECT id, category, amount, created_at
                FROM transactions
                WHERE user_id = %s AND type = %s;
                """,
                (user_id, transaction_type),
            )
            transactions = [
                {
                    "id": row[0],
                    "category": row[1],
                    "amount": row[2],
                    "created_at": row[3].strftime("%Y-%m-%d %H:%M:%S"),
                }
                for row in cursor.fetchall()
            ]
            response = {"status": "success", "transactions": transactions}
        else:
            response = {"status": "error", "error": "Invalid command"}

        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        response = {"status": "error", "error": str(e)}

    # Отправляем ответ обратно
    ch.basic_publish(
        exchange="",
        routing_key=properties.reply_to,
        properties=pika.BasicProperties(correlation_id=properties.correlation_id),
        body=json.dumps(response),
    )
    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()

    # Объявляем очередь
    channel.queue_declare(queue="task_queue")
    print("Server is waiting for messages...")

    # Слушаем запросы
    channel.basic_consume(queue="task_queue", on_message_callback=handle_request)
    channel.start_consuming()


if __name__ == "__main__":
    main()
