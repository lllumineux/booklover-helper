from dbase import db


# Таблица пользователей
class User(db.Model):
    # ID пользователя в базе данных приложения
    id = db.Column(db.Integer, primary_key=True)

    # ID пользователя, выданный Алисой
    alice_id = db.Column(db.String(1000), unique=True, nullable=False)

    # Имя пользователя, которое он указывает сам
    name = db.Column(db.String(1000), nullable=False)

    # Представление таблицы в виде класса
    def __repr__(self):
        return '<User {} {} {}>'.format(
            self.id,
            self.alice_id,
            self.name
        )

    # Функция добавления нового пользователя (обязательно нужно указать id)
    @staticmethod
    def add(user_id, user_name):
        user = User(
            id=user_id,
            name=user_name
        )
        db.session.add(user)
        db.session.commit()

    # Функция удаления пользователя
    @staticmethod
    def delete(user):
        db.session.delete(user)
        db.session.commit()


# Таблица книг
class Book(db.Model):
    # ID пользователя в базе данных приложения
    id = db.Column(db.Integer, primary_key=True)

    # Привязка книги к конкретному пользователю
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('book_list', lazy=True))

    # ID книги в библиотеке Google книг
    google_id = db.Column(db.String(1000), unique=True, nullable=False)

    # Статус книги:
    # 0 - книга в списке желаемых к прочтению
    # 1 - книга в списке читаемых в данный момент
    # 2 - книга в списке прочитанных
    status = db.Column(db.Integer, nullable=False)

    # Представление таблицы в виде класса
    def __repr__(self):
        return '<Book {} {} {} {}>'.format(
            self.id,
            self.user_id,
            self.google_id,
            self.status
        )

    # Функция добавления новой книги (обязательно нужно указать id)
    @staticmethod
    def add(user, book_id):
        book = Book(
            user=user,
            id=book_id
        )
        db.session.add(book)
        db.session.commit()

    # Функция изменения статуса книги
    @staticmethod
    def change_status(book, book_new_status):
        book.status = book_new_status
        db.session.commit()

    # Функция удаления книги из всех списков
    @staticmethod
    def delete(book):
        db.session.delete(book)
        db.session.commit()


# Таблица закладок
class Bookmark(db.Model):
    # ID пользователя в базе данных приложения
    id = db.Column(db.Integer, primary_key=True)

    # Привязка закладки к конкретной книге, котороя находится в списке
    # "читаемое в данный момент"
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    book = db.relationship('Book', backref=db.backref('bookmark_list', lazy=True))

    # Страница, на которой находится закладка
    page = db.Column(db.String(1000), unique=True, nullable=False)

    # Название закладки, задаётся пользователем
    title = db.Column(db.String(1000), nullable=False)

    # Представление таблицы в виде класса
    def __repr__(self):
        return '<Bookmark {} {} {} {}>'.format(
            self.id,
            self.book_id,
            self.page,
            self.title
        )

    # Функция добавления новой закладки
    @staticmethod
    def add(book, bookmark_page, bookmark_title):
        bookmark = Book(
            book=book,
            page=bookmark_page,
            title=bookmark_title
        )
        db.session.add(bookmark)
        db.session.commit()

    # Функция удаления закладки
    @staticmethod
    def delete(bookmark):
        db.session.delete(bookmark)
        db.session.commit()
