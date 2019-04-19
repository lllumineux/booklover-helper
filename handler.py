from flask import request
from models import User, Book, Bookmark
import requests
import logging
import json


def init_route(app, db):
    # Создание лог-файла и обозначение формы записи логов
    logging.basicConfig(
        level=logging.INFO,
        filename='app.log',
        format='%(asctime)s %(levelname)s %(name)s %(message)s'
    )

    # Значение api ключа
    google_api_key = 'AIzaSyACUmqyAmi8O61eikdpdlRniTP_Iga-L0A'
    google_books_api_url = 'https://www.googleapis.com/books/v1/volumes'

    # Декоратор приёма post запроса
    @app.route('/', methods=['POST'])
    def main():
        # Создание таблиц в базе данных, если они ещё не созданы
        db.create_all()

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

    # Функция обработки запроса и создания ответа
    def handle_dialog(res, req):
        try:
            res['response']['text'] = '*робит*'
        except Exception as e:
            print(e)
