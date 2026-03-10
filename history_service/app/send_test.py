#!!!!!!!!!!! братани, це файл скрипт для тестування. Для імітації надсилання повідомлення та відповідно перевірки listener
# ----------------------------------^ ^----------------------------------
import pika
import json

# Підключаємося до RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
channel = connection.channel()

# Оголошуємо чергу (про всяк випадок)
channel.queue_declare(queue='history_queue', durable=True)

# Дані про транзакцію, які ми кидаємо в чергу
message = {
    "sender_id": "user123",
    "receiver_id": "edvard_student",
    "amount": 1000.0,
    "currency": "UAH",
    "type": "transfer"
}

# Відправляємо
channel.basic_publish(
    exchange='',
    routing_key='history_queue',
    body=json.dumps(message),
    properties=pika.BasicProperties(delivery_mode=2) # Робимо повідомлення стійким
)

print(f" [x] Відправлено тестову транзакцію: {message}")
connection.close()