from models import User, Book, Bookmark
from flask import request
import requests
import logging
import string
import random
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

        # List of request words
        req_words = [word.lower() for word in req['request']['nlu']['tokens']]

        # Response text
        response_text = ''

        try:
            # Trying to get user info from database
            user = User.query.filter_by(alice_id=session_storage['alice_id']).first()

            # If the user has just started the skill
            if req['session']['new']:
                # If the user uses skill for the first time
                if user:
                    res['response']['text'] = 'Hello, {}! Do you want to see available commands?'.format(user.name)
                    session_storage['username'] = user.name
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
                    res['response']['text'] = 'Nice to meet you, {}! That\'s what I can:\n{}'.format(name, '\n'.join(possibilities))
                    session_storage['username'] = name
                    session_storage['current_theme'] = 'what_to_do'

            # If the user was asked "Do you need instructions?"
            elif session_storage['current_theme'] == 'need_instruction':
                for word in ['yes']:
                    # If one of positive words is in request word list
                    if word in req_words:
                        res['response']['text'] = 'That\'s what I can:\n{}'.format(
                            '\n'.join(possibilities)
                        ) + '\nWhat do you want me to do?'
                        session_storage['current_theme'] = 'what_to_do'
                for word in ['no']:
                    # If one of negative words is in request word list
                    if word in req_words:
                        res['response']['text'] = 'Ok! What can I do for you?'
                        session_storage['current_theme'] = 'what_to_do'

            # If the user was asked "What to do?"
            elif session_storage['current_theme'] == 'what_to_do':
                if 'book' in req_words:
                    book_name, book_author, book_category = '', '', ''

                    # Getting book name
                    if 'called' in req_words:
                        book_name = ' '.join(
                            req_words[req_words.index('called') + 1:req_words.index('by'):] if 'by' in req_words
                            else req_words[req_words.index('called') + 1::]
                        ).capitalize()

                    # Getting book author
                    if 'by' in req_words:
                        if 'on' in req_words:
                            book_author = ' '.join(
                                req_words[req_words.index('by') + 1:req_words.index('on'):]
                            ).capitalize()
                        elif 'in' in req_words:
                            book_author = ' '.join(
                                req_words[req_words.index('by') + 1:req_words.index('in'):]
                            ).capitalize()
                        elif 'to' in req_words:
                            book_author = ' '.join(
                                req_words[req_words.index('by') + 1:req_words.index('to'):]
                            ).capitalize()
                        elif 'from' in req_words:
                            book_author = ' '.join(
                                req_words[req_words.index('by') + 1:req_words.index('from'):]
                            ).capitalize()
                        else:
                            book_author = ' '.join(
                                req_words[req_words.index('by') + 1::]
                            ).capitalize()

                    # Getting book category
                    if 'in' in req_words and 'category' in req_words:
                        book_category = ' '.join(
                            req_words[req_words.index('in') + 1:req_words.index('category'):]
                        ).capitalize()

                    # If user asked for a random book
                    if 'random' in req_words:
                        # Picking random letter
                        letter = random.choice([let for let in string.ascii_letters])
                        # Picking random book
                        while not response_text:
                            book = random.choice(get_book_list(text=letter))
                            response_text = get_response_text_from_book(book)
                        res['response']['text'] = response_text + '\n\n\nWhat else I can do for you, {}?'.format(session_storage['username'])

                    # If user wants to add book in the list
                    elif 'list' in req_words:
                        # Getting list type
                        list_type = -1
                        if 'wish' in req_words:
                            list_type = 0
                        elif 'now' in req_words and 'reading' in req_words:
                            list_type = 1
                        elif 'already' in req_words and 'read' in req_words:
                            list_type = 2
                        # If list type is not correct
                        if list_type == -1:
                            response_text = 'Specified list not found!'
                            res['response']['text'] = response_text
                            return
                        # If user wants to add book in list
                        if 'add' in req_words and 'to' in req_words:
                            # If all data is correct
                            if book_name and book_author and list_type != -1:
                                user = User.query.filter_by(
                                    alice_id=session_storage['alice_id']
                                ).first()
                                book = Book.query.filter_by(
                                    title=book_name,
                                    author=book_author
                                ).first()
                                if book:
                                    response_text = 'Book already in \"{}\" list!'.format(
                                        ['Wish', 'Now reading', 'Already read'][book.status]
                                    )
                                    res['response']['text'] = response_text
                                else:
                                    books = list(Book.query.filter_by(
                                        status=list_type
                                    ))
                                    if len(books) >= 5:
                                        res['response']['text'] = 'You can\'t add more than 5 books in one list!'
                                    else:
                                        Book.add(user, book_name, book_author, list_type)
                                        res['response']['text'] = 'Book has been added!' + '\n\n\nWhat else I can do for you, {}?'.format(session_storage['username'])

                        # If user wants to delete book from list
                        elif 'delete' in req_words and 'from' in req_words:
                            # If all data is correct
                            if book_name and book_author and list_type != -1:
                                book = Book.query.filter_by(
                                    title=book_name,
                                    author=book_author,
                                    status=list_type
                                ).first()
                                if book:
                                    Book.delete(book)
                                    res['response']['text'] = 'Book has been deleted!' + '\n\n\nWhat else I can do for you, {}?'.format(session_storage['username'])
                                else:
                                    response_text = 'No such book in \"{}\" list!'.format(
                                        ['Wish', 'Now reading', 'Already read'][list_type]
                                    )
                                    res['response']['text'] = response_text

                    # If any of parameters exist
                    elif any([book_name, book_author, book_category]):
                        # Get book by parameters
                        book = random.choice(get_book_list(
                            title=book_name,
                            author=book_author,
                            category=book_category
                        ))
                        # Get response text
                        response_text = get_response_text_from_book(book)
                        if response_text:
                            res['response']['text'] = response_text + '\n\n\nWhat else I can do for you, {}?'.format(session_storage['username'])
                            session_storage['current_theme'] = 'what_to_do'

                if 'books' in req_words and 'from' in req_words and 'list' in req_words:
                    # Getting list type
                        list_type = -1
                        if 'wish' in req_words:
                            list_type = 0
                        elif 'now' in req_words and 'reading' in req_words:
                            list_type = 1
                        elif 'already' in req_words and 'read' in req_words:
                            list_type = 2
                        if list_type != -1:
                            # Getting user
                            user = User.query.filter_by(
                                alice_id=session_storage['alice_id']
                            ).first()
                            # Getting book list
                            books = [book for book in Book.query.filter_by(
                                user_id=user.id,
                                status=list_type
                            )]
                            # If chosen list has books in it
                            if books:
                                response_text = '\n\n\n'.join([
                                    'Title:\n{}\n\n\nAuthor:\n{}'.format(
                                        book.title,
                                        book.author
                                    ) for book in books
                                ])
                                res['response']['text'] = response_text
                            # If no books found in chosen list
                            else:
                                response_text = '\"{}\" list is empty!'.format(
                                    ['Wish', 'Now reading', 'Already read'][list_type]
                                )
                                res['response']['text'] = response_text
                        else:
                            response_text = 'Specified list not found!'
                            res['response']['text'] = response_text
                # If user asks to tell him what bot can do
                elif 'what' in req_words and 'can' in req_words:
                    res['response']['text'] = 'That\'s what I can:\n{}'.format(
                        '\n'.join(possibilities)
                    ) + '\nWhat do you want me to do?'
        except Exception as e:
            print(e)
        # If no response text was picked or an error occurred
        if res['response']['text'] == '':
            res['response']['text'] = 'Repeat, please!'

    # The function of finding the name in the request words list
    def get_name(req):
        try:
            # List of request words
            req_words = req['request']['nlu']['tokens']

            # Name searching
            if len(req_words) == 1:
                return req_words[0]
            for i in range(len(req_words)):
                if req_words[i].lower() in ['is']:
                    return req_words[i + 1]
        except Exception as e:
            print(e)
        return None

    # Function that returns a list of books by specified parameters
    def get_book_list(text='', title='', author='', category='', max_res_amount=40):
        try:
            if 1 <= max_res_amount <= 40:
                # The request parameters to Google Books
                google_books_params = {
                    'q': '+'.join(
                        list(filter(
                            lambda x: x != '',
                            ('{}'.format(text) if text != '' else '',
                             'intitle:{}'.format(title) if title != '' else '',
                             'inauthor:{}'.format(author) if author != '' else '',
                             'subject:{}'.format(category) if category != '' else '')
                        ))
                    ),
                    'maxResults': str(max_res_amount) if 1 <= max_res_amount <= 40 else '40',
                    'langRestrict': 'en',
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

    # Function that returns a books by Google Books id
    def get_book(book_id):
        try:
            # Request to Google Books
            google_books_res = requests.get('{}/{}'.format(google_books_api_url, book_id))

            if google_books_res:
                # json response from server
                google_books_json_res = google_books_res.json()
                return google_books_json_res
        except Exception as e:
            print(e)
        return None

    # Function that makes response text from book
    def get_response_text_from_book(book):
        try:
            book_title = book['volumeInfo']['title']
            book_authors = book['volumeInfo']['authors']
            book_description = book['volumeInfo']['description'].split('.')[0] + '.'

            return '\n\n\n'.join((
                'Title:\n' + book_title,
                'Authors:\n' + '\n'.join(book_authors),
                'Description:\n' + book_description[:750:]
            ))
        except Exception as e:
            print(e)
        return None
