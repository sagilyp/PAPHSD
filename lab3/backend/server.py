import pika
import json
import database
from decimal import Decimal
from datetime import datetime


def custom_serializer(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

RABBITMQ_HOST = 'rabbitmq'

REGISTER_QUEUE = 'register_queue'
LOGIN_QUEUE = 'login_queue'
TRANSACTION_QUEUE = 'transaction_queue'
TRANSACTION_GET_QUEUE = 'transaction_get_queue'
DELETE_TRANSACTION_QUEUE = 'delete_transaction_queue'
DELETE_USER_QUEUE = 'delete_user_queue'


def respond(ch, properties, response):
    """Отправляет ответ на RPC-запрос."""
    ch.basic_publish(
        exchange='',
        routing_key=properties.reply_to,
        body=json.dumps(response, default=custom_serializer),
        properties=pika.BasicProperties(
            correlation_id=properties.correlation_id
        )
    )

def register_callback(ch, method, properties, body):
    """Обработка запросов на регистрацию."""
    message = json.loads(body)
    username = message['username']
    password = message['password']
    response = {}
    try:
        user_id = database.create_user(username, password)
        response = {'status': 'success', 'user_id': user_id}
        print(f"User {username} registered with ID {user_id}.")
    except Exception as e:
        response = {'status': 'failure', 'error': str(e)}
        print(f"Registration failed: {e}")
    respond(ch, properties, response)
    ch.basic_ack(delivery_tag=method.delivery_tag)

def delete_user_callback(ch, method, properties, body):
    """Обработка запросов на удаление пользователя."""
    message = json.loads(body)
    user_id = message['user_id']
    response = {}
    try:
        database.delete_user(user_id)
        response = {'status': 'success'}
        print(f"User {user_id} deleted.")
    except Exception as e:
        response = {'status': 'failure', 'error': str(e)}
        print(f"Failed to delete user {user_id}: {e}")
    respond(ch, properties, response)
    ch.basic_ack(delivery_tag=method.delivery_tag)


def login_callback(ch, method, properties, body):
    """Обработка запросов на авторизацию."""
    message = json.loads(body)
    username = message['username']
    password = message['password']
    response = {}
    user_id = database.authenticate_user(username, password)
    if user_id:
        response = {'status': 'success', 'user_id': user_id}
        print(f"User {username} authenticated with ID {user_id}.")
    else:
        response = {'status': 'failure', 'user_id': None}
        print(f"Authentication failed for user {username}.")

    respond(ch, properties, response)
    ch.basic_ack(delivery_tag=method.delivery_tag)


def transaction_callback(ch, method, properties, body):
    """Обработка транзакций."""
    message = json.loads(body)
    user_id = message['user_id']
    transaction_type = message['type']
    category = message['category']
    amount = message['amount']
    response = {}
    try:
        transaction_id = database.add_transaction(user_id, transaction_type, category, amount)
        response = {'status': 'success', 'transaction_id': transaction_id}
        print(f"Transaction {transaction_id} added for user {user_id}.")
    except Exception as e:
        response = {'status': 'failure', 'error': str(e)}
        print(f"Transaction failed: {e}")
    respond(ch, properties, response)
    ch.basic_ack(delivery_tag=method.delivery_tag)

def transaction_get_callback(ch, method, properties, body):
    """Обработка запросов на получение транзакций."""
    message = json.loads(body)
    user_id = message['user_id']
    transaction_type = message['type']
    response = {}
    try:
        transactions = database.get_transactions(user_id, transaction_type)
        response = {'status': 'success', 'transactions': transactions}
        print(f"Fetched transactions for user {user_id}: {transactions}")
    except Exception as e:
        response = {'status': 'failure', 'error': str(e)}
        print(f"Failed to fetch transactions for user {user_id}: {e}")
    respond(ch, properties, response)
    ch.basic_ack(delivery_tag=method.delivery_tag)

def transaction_delete_callback(ch, method, properties, body):
    """Обработка запросов на удаление транзакций."""
    message = json.loads(body)
    transaction_id = message['transaction_id']
    response = {}
    try:
        database.delete_transaction(transaction_id)
        response = {'status': 'success'}
        print(f"Transaction {transaction_id} deleted.")
    except Exception as e:
        response = {'status': 'failure', 'error': str(e)}
        print(f"Failed to delete transaction {transaction_id}: {e}")
    respond(ch, properties, response)
    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    """Настройка RabbitMQ и подписка на очереди."""
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()

    channel.queue_declare(queue=REGISTER_QUEUE, durable=True)
    channel.queue_declare(queue=LOGIN_QUEUE, durable=True)
    channel.queue_declare(queue=TRANSACTION_QUEUE, durable=True)
    channel.queue_declare(queue=TRANSACTION_GET_QUEUE, durable=True)
    channel.queue_declare(queue=DELETE_TRANSACTION_QUEUE, durable=True)
    channel.queue_declare(queue=DELETE_USER_QUEUE, durable=True)

    channel.basic_consume(queue=REGISTER_QUEUE, on_message_callback=register_callback)
    channel.basic_consume(queue=LOGIN_QUEUE, on_message_callback=login_callback)
    channel.basic_consume(queue=TRANSACTION_QUEUE, on_message_callback=transaction_callback)
    channel.basic_consume(queue=TRANSACTION_GET_QUEUE, on_message_callback=transaction_get_callback)
    channel.basic_consume(queue=DELETE_TRANSACTION_QUEUE, on_message_callback=transaction_delete_callback)
    channel.basic_consume(queue=DELETE_USER_QUEUE, on_message_callback=delete_user_callback)

    print("Server is waiting for messages.")
    channel.start_consuming()

if __name__ == "__main__":
    main()
