import pika
import json
import psycopg2

DB_CONFIG = {
    "dbname": "finance_db",
    "user": "user",
    "password": "password",
    "host": "db"
}

RABBITMQ_HOST = "rabbitmq"
REQUEST_QUEUE = "request_queue"

def process_request(ch, method, properties, body):
    request = json.loads(body)
    response = {}

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    try:
        if request["action"] == "register":
            cur.execute("INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id",
                        (request["username"], request["password"]))
            conn.commit()
            response = {"message": "User registered"}
        elif request["action"] == "login":
            cur.execute("SELECT id FROM users WHERE username = %s AND password = %s",
                        (request["username"], request["password"]))
            user = cur.fetchone()
            response = {"user_id": user[0]} if user else {"error": "Invalid credentials"}
        elif request["action"] == "add_transaction":
            cur.execute("INSERT INTO transactions (user_id, type, category, amount) VALUES (%s, %s, %s, %s) RETURNING id",
                        (request["user_id"], request["type"], request["category"], request["amount"]))
            conn.commit()
            response = {"message": "Transaction added"}
        elif request["action"] == "get_transactions":
            cur.execute(
                "SELECT id, created_at, type, category, amount FROM transactions WHERE user_id = %s",
                (request["user_id"],)
            )
            transactions = [
                {
                    "id": row[0],
                    "created_at": row[1].strftime('%Y-%m-%d %H:%M:%S') if row[1] else "Нет даты",
                    "type": row[2],
                    "category": row[3],
                    "amount": float(row[4])
                }
                for row in cur.fetchall()
            ]
            response = {"transactions": transactions}
        elif request["action"] == "delete_transaction":
            cur.execute("DELETE FROM transactions WHERE id = %s", (request["transaction_id"],))
            conn.commit()
            response = {"message": "Transaction deleted"}
    except Exception as e:
        response = {"error": str(e)}
    finally:
        conn.close()

    ch.basic_publish(
        exchange='',
        routing_key=properties.reply_to,
        properties=pika.BasicProperties(correlation_id=properties.correlation_id),
        body=json.dumps(response)
    )
    ch.basic_ack(delivery_tag=method.delivery_tag)

connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
channel = connection.channel()
channel.queue_declare(queue=REQUEST_QUEUE, durable=True)

channel.basic_consume(queue=REQUEST_QUEUE, on_message_callback=process_request)

print("Backend is waiting for requests...")
channel.start_consuming()
