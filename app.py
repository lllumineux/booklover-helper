from flask import Flask, request
import requests
import logging
import json

# Создание фласк приложения
app = Flask(__name__)
app.config['SECRET_KEY'] = 'kyXchNb6A3VhCFoBBuTOaCP1'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///main.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Создание лог-файла и обозначение формы записи логов
logging.basicConfig(
    level=logging.INFO,
    filename='app.log',
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)

# Значение google api ключа
google_api_key = 'AIzaSyACUmqyAmi8O61eikdpdlRniTP_Iga-L0A'
google_books_api_url = 'https://www.googleapis.com/books/v1/volumes'


# Декоратор приёма post запроса на index-page
@app.route('/', methods=['POST'])
def main():
    # Создание лога с информацией о запросе
    logging.info('Request: %r', request.json)

    # Обработка запроса
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)

    # Создание лога с информацией об ответе
    logging.info('Request: %r', response)

    # Отправка ответа в формате json
    return json.dumps(response)


# Функция модифицирования ответа на основе запроса
def handle_dialog(res, req):
    try:
        pass
    except Exception as e:
        print(e)
