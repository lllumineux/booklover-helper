from models import User
from flask import request
import logging
import json
import handler_functions


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

        # List of request words
        req_words = [word.lower() for word in req['request']['nlu']['tokens']]

        # Response text
        response_text = ''

        try:
            # Trying to get user info from database
            user = User.query.filter_by(alice_id=session_storage['alice_id']).first()

            # If the user has just started the skill
            if req['session']['new']:
                handler_functions.new_session_handler(res, user, session_storage)

            # If the user was asked "What is your name?"
            if session_storage['current_theme'] == 'user_name':
                handler_functions.user_name_handler(req, res, session_storage)

            # If the user was asked "Do you need instructions?"
            elif session_storage['current_theme'] == 'need_instruction':
                handler_functions.instruction_handler(req_words, res, session_storage)

            # If the user was asked "What to do?"
            elif session_storage['current_theme'] == 'what_to_do':
                handler_functions.what_to_do_handler(req_words, response_text, res, session_storage)

        except Exception as e:
            print(e)

        # If no response text was picked or an error occurred
        if res['response']['text'] == '':
            res['response']['text'] = 'Repeat, please!'
