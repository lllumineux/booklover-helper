import random
import string
import requests
from models import User, Book, Bookmark


# API link and it's key
google_books_api_url = 'https://www.googleapis.com/books/v1/volumes'
google_api_key = 'AIzaSyACUmqyAmi8O61eikdpdlRniTP_Iga-L0A'

# What bot can do for user:
possibilities = [
    '1)Show random book',
    '2)Show book called *title*',
    '3)Show book by *author*',
    '4)Show book in *category* category',
    '5)Add book called *title* by *author* to wish/reading now/already read list',
    '6)Delete book called *title* by *author* from wish/reading now/already read list',
    '7)Show all books from wish/reading now/already list',
    '8)Add bookmark in book called *title* by *author* on page *page* and name it *title*',
    '9)Delete bookmark from book called *title* by *author* on page *page*',
    '10)Show bookmarks from book called *title* by *author*'
]


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


def get_book_info(req_words):
    try:
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
            elif 'from' in req_words and 'bookmarks' not in req_words:
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

        return {
            'book_name': book_name,
            'book_author': book_author,
            'book_category': book_category
        }
    except Exception as e:
        print(e)


def get_bookmark_info(req_words):
    bookmark_page, bookmark_title = '', ''
    for num in range(len(req_words)):
        # Trying to find bookmark page
        if req_words[num] == 'on' and req_words[num + 1] == 'page':
            bookmark_page = req_words[num + 2]
        # Trying to find bookmark title
        if 'name' in req_words:
            if req_words[num] == 'name' and req_words[num + 1] == 'it':
                bookmark_title = ' '.join(req_words[num + 2::])

    return {
        'bookmark_page': bookmark_page,
        'bookmark_title': bookmark_title
    }


def get_list_type(req_words, res):
    try:
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
        return list_type
    except Exception as e:
        print(e)


def new_session_handler(res, user, session_storage):
    try:
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
    except Exception as e:
        print(e)


def user_name_handler(req, res, session_storage):
    try:
        name = get_name(req)
        # If name is found in the request
        if name:
            name = name.capitalize()
            # New user creating
            User.add(session_storage['alice_id'], name)
            res['response']['text'] = 'Nice to meet you, {}! That\'s what I can:\n{}'.format(name, '\n\n\n'.join(possibilities))
            session_storage['username'] = name
            session_storage['current_theme'] = 'what_to_do'
    except Exception as e:
        print(e)


def instruction_handler(req_words, res, session_storage):
    try:
        for word in ['yes']:
            # If one of positive words is in request word list
            if word in req_words:
                res['response']['text'] = 'That\'s what I can:\n{}'.format(
                    '\n\n\n'.join(possibilities)
                ) + '\nWhat do you want me to do?'
                session_storage['current_theme'] = 'what_to_do'
        for word in ['no']:
            # If one of negative words is in request word list
            if word in req_words:
                res['response']['text'] = 'Ok! What can I do for you?'
                session_storage['current_theme'] = 'what_to_do'
    except Exception as e:
        print(e)


def add_bookmark_handler(book_info, bookmark_info, session_storage, res):
    try:
        # If all data is correct
        if book_info['book_name'] and book_info['book_author'] and bookmark_info['bookmark_page'] and bookmark_info['bookmark_title']:
            book = Book.query.filter_by(
                title=book_info['book_name'],
                author=book_info['book_author']
            ).first()
            # If book in any list
            if book:
                # If book in now reading list
                if book.status == 1:
                    Bookmark.add(book, bookmark_info['bookmark_page'], bookmark_info['bookmark_title'])
                    res['response']['text'] = 'Bookmark has been added!' + '\n\n\nWhat else I can do for you, {}?'.format(session_storage['username'])
                # If book not in now reading list
                else:
                    res['response']['text'] = 'Chosen book should be in \"Reading now\" list!'
            # If book not found in any of lists
            else:
                res['response']['text'] = 'No such book found!'
    except Exception as e:
        print(e)


def delete_bookmark_handler(book_info, bookmark_info, session_storage, res):
    try:
        # If all data is correct
            if book_info['book_name'] and book_info['book_author'] and bookmark_info['bookmark_page']:
                book = Book.query.filter_by(
                    title=book_info['book_name'],
                    author=book_info['book_author']
                ).first()
                # If book in any list
                if book:
                    # If book in now reading list
                    if book.status == 1:
                        bookmark = Bookmark.query.filter_by(
                            book_id=book.id,
                            page=bookmark_info['bookmark_page']
                        ).first()
                        Bookmark.delete(bookmark)
                        res['response']['text'] = 'Bookmark has been deleted!' + '\n\n\nWhat else I can do for you, {}?'.format(session_storage['username'])
                    # If book not in now reading list
                    else:
                        res['response']['text'] = 'Chosen book should be in \"Reading now\" list!'
                # If book not found in any of lists
                else:
                    res['response']['text'] = 'No such book found!'
    except Exception as e:
        print(e)


def get_bookmarks_handler(book_info, res):
    try:
        # Getting book
        book = Book.query.filter_by(
            title=book_info['book_name'],
            author=book_info['book_author']
        ).first()
        if book:
            # Getting bookmarks list Show bookmarks from book called *title* by *author*
            bookmarks = [book for book in Bookmark.query.filter_by(
                book_id=book.id
            )]
            # If chosen book has bookmarks in it
            if bookmarks:
                response_text = '\n\n\n'.join([
                    'Page:\n{}\n\n\nTitle:\n{}'.format(
                        bookmark.page,
                        bookmark.title
                    ) for bookmark in bookmarks
                ])
                res['response']['text'] = response_text
            # If no bookmarks found in chosen book
            else:
                res['response']['text'] = 'No bookmarks in this book!'
        else:
            response_text = 'Specified book not found!'
            res['response']['text'] = response_text
    except Exception as e:
        print(e)


def add_book_to_list_handler(book_info, list_type, session_storage, res):
    try:
        # If all data is correct
        if book_info['book_name'] and book_info['book_author'] and list_type != -1:
            # Getting user
            user = User.query.filter_by(
                alice_id=session_storage['alice_id']
            ).first()
            # Getting book
            book = Book.query.filter_by(
                title=book_info['book_name'],
                author=book_info['book_author']
            ).first()
            # If book already in some list
            if book:
                response_text = 'Book already in \"{}\" list!'.format(
                    ['Wish', 'Now reading', 'Already read'][book.status]
                )
                res['response']['text'] = response_text
            # If book not in lists
            else:
                books = list(Book.query.filter_by(
                    status=list_type
                ))
                # If list consists from 5 books
                if len(books) >= 5:
                    res['response']['text'] = 'You can\'t add more than 5 books in one list!'
                # If list consists from less than 5 books
                else:
                    Book.add(user, book_info['book_name'], book_info['book_author'], list_type)
                    res['response']['text'] = 'Book has been added!' + '\n\n\nWhat else I can do for you, {}?'.format(session_storage['username'])
    except Exception as e:
        print(e)


def delete_book_from_list_handler(book_info, list_type, res, session_storage):
    try:
        # If all data is correct
        if book_info['book_name'] and book_info['book_author'] and list_type != -1:
            book = Book.query.filter_by(
                title=book_info['book_name'],
                author=book_info['book_author'],
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
    except Exception as e:
        print(e)


def get_book_by_parameters_handler(book_info, res, session_storage):
    try:
        # Get book by parameters
        book = random.choice(get_book_list(
            title=book_info['book_name'],
            author=book_info['book_author'],
            category=book_info['book_category']
        ))
        # Get response text
        response_text = get_response_text_from_book(book)
        if response_text:
            res['response']['text'] = response_text + '\n\n\nWhat else I can do for you, {}?'.format(session_storage['username'])
            session_storage['current_theme'] = 'what_to_do'
    except Exception as e:
        print(e)


def get_book_from_list_handler(req_words, res, session_storage):
    get_list_type(req_words, res)
    # Getting list type
    list_type = get_list_type(req_words, res)
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


def what_to_do_handler(req_words, response_text, res, session_storage):
    if 'book' in req_words:
        book_info = get_book_info(req_words)
        # If user asked for a random book
        if 'random' in req_words:
            random_book_handler(response_text, res, session_storage)

        elif 'bookmark' in req_words and 'page' in req_words:
            # Bookmark info
            bookmark_info = get_bookmark_info(req_words)

            # If user wants to add bookmark
            if 'add' in req_words:
                add_bookmark_handler(book_info, bookmark_info, session_storage, res)
            # If user wants to delete bookmark
            elif 'delete' in req_words:
                delete_bookmark_handler(book_info, bookmark_info, session_storage, res)

        # If user wants to see all the bookmarks
        elif 'bookmarks' in req_words and 'from' in req_words:
            get_bookmarks_handler(book_info, res)

        # If user wants to do something with the list
        elif 'list' in req_words:
            # Type of chosen list
            list_type = get_list_type(req_words, res)

            # If user wants to add book in list
            if 'add' in req_words and 'to' in req_words:
                add_book_to_list_handler(book_info, list_type, session_storage, res)

            # If user wants to delete book from list
            elif 'delete' in req_words and 'from' in req_words:
                delete_book_from_list_handler(book_info, list_type, res, session_storage)

        # If any of parameters exist
        elif any([book_info['book_name'], book_info['book_author'], book_info['book_category']]):
            get_book_by_parameters_handler(book_info, res, session_storage)

    elif 'books' in req_words and 'from' in req_words and 'list' in req_words:
        get_book_from_list_handler(req_words, res, session_storage)

    # If user asks to tell him what bot can do
    elif 'what' in req_words and 'can' in req_words:
        res['response']['text'] = 'That\'s what I can:\n{}'.format(
            '\n\n\n'.join(possibilities)
        ) + '\nWhat do you want me to do?'


def random_book_handler(response_text, res, session_storage):
    try:
        # Picking random letter
        letter = random.choice([let for let in string.ascii_letters])
        # Picking random book
        while not response_text:
            book = random.choice(get_book_list(text=letter))
            response_text = get_response_text_from_book(book)
        res['response']['text'] = response_text + '\n\n\nWhat else I can do for you, {}?'.format(session_storage['username'])
    except Exception as e:
        print(e)


def bookmark_add_handler(response_text, res, session_storage):
    try:
        # Picking random letter
        letter = random.choice([let for let in string.ascii_letters])
        # Picking random book
        while not response_text:
            book = random.choice(get_book_list(text=letter))
            response_text = get_response_text_from_book(book)
        res['response']['text'] = response_text + '\n\n\nWhat else I can do for you, {}?'.format(session_storage['username'])
    except Exception as e:
        print(e)

