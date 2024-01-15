import os
from datetime import timedelta

from flask import Flask, render_template, request, redirect, flash, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from models import db, User, Loan, hash_password

# app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("PEPPER", "VERY_SECRET_AND_COMPLEX_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///../db/project.db"
db.init_app(app)
with app.app_context():
    db.create_all()

# login manager
login_manager = LoginManager(app)
login_manager.login_view = 'hello_world'


@login_manager.user_loader
def load_user(username):
    return User.query.filter_by(username=username).first()


@app.route('/')
def hello_world():
    return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = load_user(username)
    if not user or hash_password(password, user.salt) != user.password:
        flash('Login unsuccessful. Please check your username and password.', 'danger')
        return render_template('index.html')

    login_user(user)
    return redirect(url_for('home'))


@app.route('/home', methods=['GET'])
@login_required
def home():
    return render_template('home.html', user=current_user)


@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    second_password = request.form['password-repeat']
    first_name, last_name = request.form['firstname'], request.form['lastname']

    if password != second_password or User.query.filter_by(username=username).first():
        flash('Register unsuccessful.', 'danger')
        return render_template('index.html')

    user = User(username, first_name, last_name, password)
    user.add_to_db()
    login_user(user, duration=timedelta(hours=1))
    return render_template("snippets/recovery_password.html", user=user), 201


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('index.html')


@app.route('/summary', methods=['GET'])
@login_required
def summary():
    loans_given = Loan.query.filter_by(lender_id=current_user.id).all()
    loans_taken = Loan.query.filter_by(borrower_id=current_user.id).all()
    return render_template('snippets/user_summary.html', loans_given=loans_given, loans_taken=loans_taken)


@app.route('/messages', methods=['GET', 'POST'])
@login_required
def messages():
    return render_template('snippets/messages.html')


@app.route('/new-loan', methods=['GET', 'POST'])
@login_required
def new_loan():
    if request.method == 'GET':
        return render_template('snippets/new_loan.html')
    if request.method == 'POST':
        borrower = User.query.filter_by(username=request.form['borrower']).first()
        if not borrower:
            flash('No such user.', 'danger')
            return render_template('snippets/new_loan.html')

        loan = Loan(current_user.id, borrower.id, request.form['amount'], request.form['deadline'])
        loan.add_to_db()
        return render_template('snippets/new_loan.html', success=True)
    return redirect(url_for('home'))


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'GET':
        return render_template('snippets/settings.html')
    if request.method == 'POST':
        first_name, last_name = request.form['first-name'], request.form['last-name']

        if not first_name or not last_name:
            flash('First name or last name cannot be empty.', 'danger')
            return render_template('snippets/settings.html')

        if current_user.first_name == first_name and current_user.last_name == last_name:
            flash('Nothing to change.', 'info')
            return render_template('snippets/settings.html')

        current_user.first_name = first_name
        current_user.last_name = last_name
        db.session.commit()
        flash('Name changed successfully.', 'success')
        return render_template('snippets/settings.html', success=True)
    return redirect(url_for('home'))


@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    old_password = request.form['password']
    new_password = request.form['new-password']
    second_new_password = request.form['new-password-repeat']

    if new_password != second_new_password or hash_password(old_password, current_user.salt) != current_user.password:
        flash('Passwords do not match.', 'danger')
        return render_template('snippets/settings.html')

    current_user.password = hash_password(new_password, current_user.salt)
    db.session.commit()
    flash('Password changed successfully.', 'success')
    return render_template('snippets/settings.html', success=True)


@app.route('/messages', methods=['GET'])
@login_required
def messages():
    user = current_user
    return render_template('snippets/messages.html')


@app.route('/loans', methods=['GET', 'POST'])
@login_required
def loans():
    if request.method == 'GET':
        loans = Loan.query.filter_by(borrower_id=current_user.id).all()
        return render_template('snippets/loans.html', loans=loans)
    if request.method == 'POST':
        loan_id = request.form['loan-id']
        loan = Loan.query.filter_by(id=loan_id).first()
        if not loan:
            flash('No such loan.', 'danger')
            return render_template('snippets/loans.html')

        loan.delete_from_db()
        return redirect(url_for('loans'))
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
