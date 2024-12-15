import pika
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import uuid
import time

RABBITMQ_HOST = 'rabbitmq'
REGISTER_QUEUE = 'register_queue'
LOGIN_QUEUE = 'login_queue'
TRANSACTION_QUEUE = 'transaction_queue'
TRANSACTION_GET_QUEUE = 'transaction_get_queue'
DELETE_TRANSACTION_QUEUE = 'delete_transaction_queue'
DELETE_USER_QUEUE = 'delete_user_queue'

class RpcClient:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.callback_queue = None
        self.connect()

    def connect(self):
        """Подключаемся к RabbitMQ и создаем канал."""
        while True:
            try:
                self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, heartbeat=60))
                self.channel = self.connection.channel()
                result = self.channel.queue_declare(queue='', exclusive=True)
                self.callback_queue = result.method.queue
                self.channel.basic_consume(
                    queue=self.callback_queue,
                    on_message_callback=self.on_response,
                    auto_ack=True
                )
                print("Connection to RabbitMQ established.")
                break
            except pika.exceptions.AMQPConnectionError as e:
                print(f"Connection failed, retrying in 5 seconds... {e}")
                time.sleep(5)  # Повторная попытка подключения через 5 секунд
    def on_response(self, ch, method, properties, body):
        """Обрабатывает ответы, соответствующие текущему запросу."""
        if properties.correlation_id == self.correlation_id:
            self.response = json.loads(body)

    def call(self, queue_name, message):
        """Отправляет сообщение и ожидает ответа."""
        self.response = None
        self.correlation_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.correlation_id,
                delivery_mode=2
            )
        )
        while self.response is None:
            try:
                self.connection.process_data_events()
            except pika.exceptions.AMQPConnectionError:
                print("Connection lost, reconnecting...")
                self.connect()
        return self.response


rpc_client = RpcClient()

class RequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Обработка POST-запросов от клиента."""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        message = json.loads(post_data)

        if self.path == '/api/register':
            response = rpc_client.call(REGISTER_QUEUE, message)
            if response.get('status') == 'success':
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
            else:
                self.send_response(401)
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())

        elif self.path == '/api/login':
            response = rpc_client.call(LOGIN_QUEUE, message)
            if response.get('status') == 'success':
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
            else:
                self.send_response(401)
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())


        elif self.path == '/api/transaction':
            response = rpc_client.call(TRANSACTION_QUEUE, message)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        """Обработка GET-запросов от клиента."""
        if self.path.startswith('/api/transactions'):
            query_params = self.path.split('?')[1].split('&')
            params = {key: value for key, value in (param.split('=') for param in query_params)}
            user_id = params.get('user_id')
            transaction_type = params.get('type')

            message = {'user_id': user_id, 'type': transaction_type}
            response = rpc_client.call(TRANSACTION_GET_QUEUE, message)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

        else:
            self.send_response(404)
            self.end_headers()

    def do_DELETE(self):
        """Обработка DELETE-запросов от клиента."""
        if self.path.startswith('/api/user/'):
            user_id = self.path.split('/')[-1]
            response = rpc_client.call('delete_user_queue', {'user_id': user_id})
            if response.get('status') == 'success':
                self.send_response(200)
            else:
                self.send_response(400)
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        if self.path.startswith('/api/transaction/'):
            transaction_id = self.path.split('/')[-1]
            response = rpc_client.call(DELETE_TRANSACTION_QUEUE, {'transaction_id': transaction_id})
            if response.get('status') == 'success':
                self.send_response(200)
            else:
                self.send_response(400)
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

def run(server_class=HTTPServer, handler_class=RequestHandler, port=8000):
    """Запускает сервер API Gateway."""
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting API Gateway on port {port}")
    httpd.serve_forever()

if __name__ == "__main__":
    run()
