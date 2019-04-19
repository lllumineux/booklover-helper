from flask import request
from models import User, Book, Bookmark
import requests
import logging
import json


def init_route(app, db):
    # Место хранения информации о пользователе
    session_storage = {
        # ID экземпляра приложения, в котором пользователь общается с Алисой
        'user_id': '',
        # Текущая тема диалога:
        # 'user_name' - активируется после того, как пользователю был задан вопрос "Как вас зовут?"
        # 'need_instruction' - активируется после того, как пользователю был задан вопрос "Нужны ли вам инструкции?"
        # 'what_to_do' - активируется после того, как пользователю был задан вопрос "Чем могу помочь?"
        'current_theme': ''
    }

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
        # Добавление id пользователя в
        session_storage['user_id'] = req['session']['user_id']

        try:
            user = User.query.filter_by(alice_id=session_storage['user_id']).first()
            # Если пользователь только запустил навык
            if req['session']['new']:
                # Если пользователь первый раз зашёл в навык
                if user:
                    res['response']['text'] = 'Здравствуйте, {}! Перечислить что могу?'.format(user.name)
                    session_storage['current_theme'] = 'need_instruction'
                # Если пользователь уже заходил в навык
                else:
                    res['response']['text'] = 'Мы не знакомы, как вас зовут?'
                    session_storage['current_theme'] = 'user_name'
                return

            # Если пользователю был задан вопрос "Как вас зовут?"
            if session_storage['current_theme'] == 'user_name':
                name = get_name(req)
                # Если фио найдены в запросе
                if name:
                    res['response']['text'] = 'Вот, что я могу: *пока тут ничего*'.format(name['first_name'])
                    User.add(session_storage['user_id'], name['first_name'].capitalize())
                # Если фио не найдены в запросе
                else:
                    res['response']['text'] = 'Повторите!'

            # Если пользователю был задан вопрос "Нужны ли вам инструкции?"
            elif session_storage['current_theme'] == 'need_instruction':
                if req['request']['original_utterance'].lower() in ['да']:
                    res['response']['text'] = 'Вот, что я могу: *пока тут ничего*'
                    session_storage['current_theme'] = 'what_to_do'
                if req['request']['original_utterance'].lower() in ['нет']:
                    res['response']['text'] = 'Что сделать?'
                    session_storage['current_theme'] = 'what_to_do'

        except Exception as e:
            print(e)

    # Функция нахождения фио среди слов в запроса
    def get_name(req):
        try:
            for entity in req['request']['nlu']['entities']:
                if entity['type'] == 'YANDEX.FIO':
                    return entity['value']
        except Exception as e:
            print(e)
        return None

    # Функция, возвращающая список книг по заданным параметрам
    def get_book_list(title='', author='', subject='', max_res_amount=40):
        try:
            # Параметры Google запроса
            google_books_params = {
                'q': '+'.join(
                    list(filter(
                        lambda x: x != '',
                        ('intitle:{}'.format(title) if title != '' else '',
                         'inauthor:{}'.format(author) if author != '' else '',
                         'subject:{}'.format(subject) if subject != '' else '')
                    ))
                ),
                'langRestrict': 'ru',
                'maxResults': str(max_res_amount) if 1 <= max_res_amount <= 40 else '40',
                'key': google_api_key
            }
            # Запрос к Google API
            google_books_res = requests.get(
                google_books_api_url,
                params=google_books_params
            )

            if google_books_res:
                # Ответ от сервера в json формате
                google_books_json_res = google_books_res.json()
                # Список из названий книг
                book_name_list = [
                    book['volumeInfo']['title']
                    for book in google_books_json_res['items']
                ]
                return book_name_list

        except Exception as e:
            print(e)
            return None
