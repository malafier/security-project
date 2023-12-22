from flask import Flask, render_template, g, request
from flask_login import LoginManager
from init_db import initialise
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

from web.user import User

# app
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://../db/project.db"

# login
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def user_loader(username):
    if not username:
        return None
    return User.query.filter_by(username=username).first()


@login_manager.request_loader
def request_loader(request):
    username = request.form.get('l-username')
    return user_loader(username)


# db
class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


@app.route('/')
def hello_world():
    return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
    username = request.form['l-username']
    password = request.form['l-password']
    user = user_loader(username)
    if not user:
        return 401
    if


@app.route('/register', methods=['POST'])
def register():
    username = request.form['r-username']
    password = request.form['r-password']
    second_password = request.form['r-password-repeat']


if __name__ == '__main__':
    initialise()
    app.run()
