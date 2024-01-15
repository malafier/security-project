import os

from flask import Flask, render_template, request, redirect, make_response, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required

from models import db, User, hash_password

# app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("PEPPER", "VERY_SECRET_AND_COMPLEX_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///../db/project.db"
db.init_app(app)
with app.app_context():
    db.create_all()

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
    username = request.form.get('username')
    return user_loader(username)


@app.route('/')
def hello_world():
    return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
    username = request.json['username']
    password = request.json['password']
    user = user_loader(username)
    if not user:
        return make_response(404, 'User not found')
    hashed_password = hash_password(password, user.salt)
    if hashed_password != user.password:
        return make_response(401, 'Wrong password')
    login_user(user)
    return render_template('home.html')


@app.route('/home', methods=['GET'])
@login_required
def home_page():
    return render_template('home.html')


@app.route('/register', methods=['POST'])
def register():
    username = request.json['username']
    password = request.json['password']
    second_password = request.json['password-repeat']
    first_name, last_name = request.json['first-name'], request.json['last-name']

    if password != second_password or User.query.filter_by(username=username).first():
        return app.response_class(
            status=400,
            body={'message': 'Something went wrong because of you'},
            mimetype='application/json'
        )

    user = User(username, first_name, last_name, password)
    user.add_to_db()
    login_user(user)
    return render_template("snippets/recovery_password.html"), 201


@app.route('/home', methods=['GET'])
@login_required
def heme_page():
    return render_template('home.html')


@app.route('/summary', methods=['GET'])
@login_required
def summary():
    return render_template('snippets')


@app.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect('index.html')


if __name__ == '__main__':
    app.run(debug=True)
