from flask import Flask
from handler import init_route
from dbase import db

# Flask application create
app = Flask(__name__)
app.config['SECRET_KEY'] = 'kyXchNb6A3VhCFoBBuTOaCP1'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqldb://lyceum73student:youngdesigngod@lyceum73student.mysql.pythonanywhere-services.com/lyceum73student$main'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Binding a database to an application
db.init_app(app)

# Main func start
init_route(app, db)

# App start
if __name__ == '__main__':
    app.run()
