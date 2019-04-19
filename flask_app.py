from flask import Flask
from handler import init_route
from dbase import db

# Создание flask приложения
app = Flask(__name__)
app.config['SECRET_KEY'] = 'kyXchNb6A3VhCFoBBuTOaCP1'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqldb://lyceum73student:youngdesigngod@lyceum73student.mysql.pythonanywhere-services.com/lyceum73student$main'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Привязка базы данных к приложению
db.init_app(app)

# Запсук главной функции
init_route(app, db)

# Запуск приложения
if __name__ == '__main__':
    app.run()
