from flask import request
from models import User, Book, Bookmark
import requests
import logging
import json


def init_route(app, db):
    # Current user info
    session_storage = {}
    # current_theme values:
    # 'user_name' - become active after "What's your name?" message
    # 'need_instruction' - become active after "Do you want to see instruction?" message
    # 'what_to_do' - become active after "How can I help you?" message

    # Creating of log-file and it's structure
    logging.basicConfig(
        level=logging.INFO,
        filename='app.log',
        format='%(asctime)s %(levelname)s %(name)s %(message)s'
    )

    # API link and it's key
    google_books_api_url = 'https://www.googleapis.com/books/v1/volumes'
    google_api_key = 'AIzaSyACUmqyAmi8O61eikdpdlRniTP_Iga-L0A'

    # What bot can do for user:
    possibilities = [
        '*Nothing here now*'
    ]

    # Post request decorator
    @app.route('/', methods=['POST'])
    def main():
        # Database tables creating
        db.create_all()

        # Creating of log with request info
        logging.info('Request: %r', request.json)

        # Response form creating
        response = {
            'session': request.json['session'],
            'version': request.json['version'],
            'response': {
                'end_session': False,
                'text': ''
            }
        }
        handle_dialog(response, request.json)

        # Creating of log with response info
        logging.info('Request: %r', response)

        # Returning json answ
        return json.dumps(response)

    # The processing function of the request and the response
    def handle_dialog(res, req):
        # Adding a user id to the database
        session_storage['alice_id'] = req['session']['user_id']

        try:
            # Trying to get user info from database
            user = User.query.filter_by(alice_id=session_storage['alice_id']).first()

            # If the user has just started the skill
            if req['session']['new']:
                # If the user uses skill for the first time
                if user:
                    res['response']['text'] = 'Hello, {}! Do you want to see available commands?'.format(user.name)
                    session_storage['current_theme'] = 'need_instruction'
                # If the user has already used the skill
                else:
                    res['response']['text'] = 'What\'s your name?'
                    session_storage['current_theme'] = 'user_name'
                return

            # If the user was asked "What is your name?"
            if session_storage['current_theme'] == 'user_name':
                name = get_name(req)
                # If name is found in the request
                if name:
                    name = name.capitalize()
                    # New user creating
                    User.add(session_storage['alice_id'], name)
                    res['response']['text'] = name.capitalize()

            # If the user was asked "Do you need instructions?"
            elif session_storage['current_theme'] == 'need_instruction':
                if req['request']['original_utterance'].lower() in ['yes']:
                    res['response']['text'] = 'That\'s what I can:\n{}'.format(
                        '\n'.join(possibilities)
                    )
                    session_storage['current_theme'] = 'what_to_do'
                if req['request']['original_utterance'].lower() in ['no']:
                    res['response']['text'] = 'Ok! what can I do for you?'
                    session_storage['current_theme'] = 'what_to_do'

            if res['response']['text'] == '':
                res['response']['text'] = 'Repeat, please!'

            print(res['response']['text'])

        except Exception as e:
            print(e)

    # The function of finding the name in the request words list
    def get_name(req):
        try:
            # List of request words
            req_words = req['request']['nlu']['tokens']

            # Name searching
            if len(req_words) == 1:
                return req_words[0]
            for i in range(len(req_words)):
                if req_words[i].lower() in ['is', 'am', '''i'm''', '''it's''', '''name's''']:
                    return req_words[i + 1]

        except Exception as e:
            print(e)
        return None

    # Function that returns a list of books by specified parameters
    def get_book_list(title='', author='', category='', max_res_amount=40):
        try:
            if 1 <= max_res_amount <= 40:
                # The request parameters to Google Books
                google_books_params = {
                    'q': '+'.join(
                        list(filter(
                            lambda x: x != '',
                            ('intitle:{}'.format(title) if title != '' else '',
                             'inauthor:{}'.format(author) if author != '' else '',
                             'subject:{}'.format(category) if category != '' else '')
                        ))
                    ),
                    'maxResults': str(max_res_amount) if 1 <= max_res_amount <= 40 else '40',
                    'key': google_api_key
                }

                # Request to Google Books
                google_books_res = requests.get(
                    google_books_api_url,
                    params=google_books_params
                )
                if google_books_res:
                    # json response from server
                    google_books_json_res = google_books_res.json()
                    return google_books_json_res['items']

        except Exception as e:
            print(e)
        return None
