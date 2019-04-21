from dbase import db


# User table
class User(db.Model):
    # User ID in the app database
    id = db.Column(db.Integer, primary_key=True)

    # User ID given by Alice
    alice_id = db.Column(db.String(1000), unique=True, nullable=False)

    # The user name that he specifies by himself
    name = db.Column(db.String(1000), nullable=False)

    # Table view as a class
    def __repr__(self):
        return '<User {} {} {}>'.format(
            self.id,
            self.alice_id,
            self.name
        )

    # Add new user function (you must specify the id)
    @staticmethod
    def add(user_alice_id, user_name):
        user = User(
            alice_id=user_alice_id,
            name=user_name
        )
        db.session.add(user)
        db.session.commit()

    # Delete user function
    @staticmethod
    def delete(user):
        db.session.delete(user)
        db.session.commit()


# Book table
class Book(db.Model):
    # User ID in the app database
    id = db.Column(db.Integer, primary_key=True)

    # Binding a book to a specific user
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('book_list', lazy=True))

    # Book ID in Google books
    google_id = db.Column(db.String(1000), unique=True, nullable=False)

    # The status of the book:
    # 0 - book in the list of wishful books
    # 1 - book in the list of now on reading books
    # 2 - book in the list of already read books
    status = db.Column(db.Integer, nullable=False)

    # Table view as a class
    def __repr__(self):
        return '<Book {} {} {} {}>'.format(
            self.id,
            self.user_id,
            self.google_id,
            self.status
        )

    # Add new book function (you must specify the id)
    @staticmethod
    def add(user, book_google_id, book_status):
        book = Book(
            user=user,
            google_id=book_google_id,
            status=book_status
        )
        db.session.add(book)
        db.session.commit()

    # The function of changing the status of the book
    @staticmethod
    def change_status(book, book_new_status):
        book.status = book_new_status
        db.session.commit()

    # Delete book from all lists function
    @staticmethod
    def delete(book):
        db.session.delete(book)
        db.session.commit()


# Bookmark table
class Bookmark(db.Model):
    # User ID in the app database
    id = db.Column(db.Integer, primary_key=True)

    # Binding a bookmark to a specific book, which is in the "now on reading" list
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    book = db.relationship('Book', backref=db.backref('bookmark_list', lazy=True))

    # The page where the bookmark is located
    page = db.Column(db.String(1000), unique=True, nullable=False)

    # The name of the bookmark which is specified by the user
    title = db.Column(db.String(1000), nullable=False)

    # Table view as a class
    def __repr__(self):
        return '<Bookmark {} {} {} {}>'.format(
            self.id,
            self.book_id,
            self.page,
            self.title
        )

    # Add new bookmark function
    @staticmethod
    def add(book, bookmark_page, bookmark_title):
        bookmark = Book(
            book=book,
            page=bookmark_page,
            title=bookmark_title
        )
        db.session.add(bookmark)
        db.session.commit()

    # Delete bookmark function
    @staticmethod
    def delete(bookmark):
        db.session.delete(bookmark)
        db.session.commit()
