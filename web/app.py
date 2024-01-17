import os
from datetime import timedelta, datetime

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
    return render_template('pages/home.html', user=current_user)


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
    return redirect(url_for('hello_world'))


@app.route('/summary', methods=['GET'])
@login_required
def summary():
    loans_given = Loan.query.filter_by(lender_id=current_user.id).all()
    loans_taken = Loan.query.filter_by(borrower_id=current_user.id).all()
    return render_template('snippets/user_summary.html', loans_given=loans_given, loans_taken=loans_taken)


@app.route('/new-loan', methods=['GET', 'POST'])
@login_required
def new_loan():
    if request.method == 'GET':
        return render_template('pages/new_loan.html')
    if request.method == 'POST':
        borrower = User.query.filter_by(username=request.form['borrower']).first()
        if not borrower:
            flash('No such user.', 'danger')
            return render_template('pages/new_loan.html')

        deadline = datetime.strptime(request.form['deadline'], '%Y-%m-%d')
        loan = Loan(current_user.id, borrower.id, request.form['amount'], deadline)
        loan.add_to_db()
        return redirect("home")
    return redirect(url_for('home'))


@app.route('/new-loan/<int:id>/accept', methods=['POST'])
@login_required
def accept_loan():
    loan = Loan.query.filter_by(id=id).first()
    if not loan:
        flash('No such loan.', 'danger')
        return render_template('pages/new_loan.html')

    loan.status_id = 2
    loan.commit()
    return redirect(url_for('home'))


@app.route('/new-loan/<int:id>/reject', methods=['POST'])
@login_required
def reject_loan():
    loan = Loan.query.filter_by(id=id).first()
    if not loan:
        flash('No such loan.', 'danger')
        return render_template('pages/new_loan.html')

    loan.status_id = 5
    loan.commit()
    return redirect(url_for('home'))


@app.route('/loan/<int:id>/repay', methods=['POST'])
@login_required
def repay_loan():
    loan = Loan.query.filter_by(id=id).first()
    if not loan:
        flash('No such loan.', 'danger')
        return render_template('pages/your_loans_debts.html')

    loan.status_id = 3
    loan.commit()
    return redirect(url_for('home'))


@app.route('/loan/<int:id>/reject', methods=['POST'])
@login_required
def reject_repayment():
    loan = Loan.query.filter_by(id=id).first()
    if not loan:
        flash('No such loan.', 'danger')
        return render_template('pages/your_loans_debts.html')

    loan.status_id = 2
    loan.commit()
    return redirect(url_for('home'))


@app.route('/loan/<int:id>/accept', methods=['POST'])
@login_required
def accept_repayment():
    loan = Loan.query.filter_by(id=id).first()
    if not loan:
        flash('No such loan.', 'danger')
        return render_template('pages/your_loans_debts.html')

    loan.status_id = 4
    loan.commit()
    return redirect(url_for('home'))


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'GET':
        return render_template('pages/settings.html')
    if request.method == 'POST':
        first_name, last_name = request.form['first-name'], request.form['last-name']

        if not first_name or not last_name:
            flash('First name or last name cannot be empty.', 'danger')
            return render_template('pages/settings.html')

        if current_user.first_name == first_name and current_user.last_name == last_name:
            flash('Nothing to change.', 'info')
            return render_template('pages/settings.html')

        current_user.first_name = first_name
        current_user.last_name = last_name
        db.session.commit()
        flash('Name changed successfully.', 'success')
        return render_template('pages/settings.html', success=True)
    return redirect(url_for('home'))


@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    old_password = request.form['password']
    new_password = request.form['new-password']
    second_new_password = request.form['new-password-repeat']

    if new_password != second_new_password or hash_password(old_password, current_user.salt) != current_user.password:
        flash('Passwords do not match.', 'danger')
        return render_template('pages/settings.html')

    current_user.password = hash_password(new_password, current_user.salt)
    db.session.commit()
    flash('Password changed successfully.', 'success')
    return render_template('pages/settings.html', success=True)


@app.route('/messages')
@login_required
def messages():
    #  user = current_user
    return 501  # render_template('snippets/messages.html')


@app.route('/logs')
@login_required
def logs():
    return 501


@app.route('/other-loans', methods=['GET', 'POST'])
@login_required
def other_loans():
    if request.method == 'GET':
        loans = Loan.query.filter_by(borrower_id=current_user.id).all()
        return render_template('pages/other_loans.html', loans=loans)
    if request.method == 'POST':
        loan_id = request.form['loan-id']
        loan = Loan.query.filter_by(id=loan_id).first()
        if not loan:
            flash('No such loan.', 'danger')
            return render_template('pages/other_loans.html')

        loan.delete_from_db()
        return redirect(url_for('loans'))
    return redirect(url_for('home'))


@app.route('/loans')
@login_required
def loans():
    loans = Loan.query.filter_by(lender_id=current_user.id).all()
    debts = Loan.query.filter_by(borrower_id=current_user.id).all()
    return render_template('pages/your_loans_debts.html', loans=loans, debts=debts)


if __name__ == '__main__':
    app.run(debug=True)
