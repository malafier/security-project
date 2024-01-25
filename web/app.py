import os
from datetime import timedelta, datetime, date

from flask import Flask, render_template, request, redirect, flash, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from user_agents import parse

import security_utils as su
from models.db_init import db
from models.loan_models import Loan, LoanMessage, Notification, NotificationType
from models.model_handler import search_users, get_all_loans, get_all_debts, loans_given, loans_taken, compare_logins, \
    get_logs
from models.user_models import User, LoginLog, LoginMonitor

# app initialization
IS_DOCKER = os.environ.get("IS_DOCKER", "False")
if IS_DOCKER == "True":
    template_dir = os.path.abspath('/web/templates/')
    db_dir = "//web/db/project.db"
    app = Flask(__name__, template_folder=template_dir)
else:
    db_dir = "../db/project.db"
    app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("PEPPER", "VERY_SECRET_AND_COMPLEX_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_dir
db.init_app(app)
with app.app_context():
    db.create_all()

# index manager
login_manager = LoginManager(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(username):
    return User.query.filter_by(username=username).first()


@app.route("/")
def hello_world():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("pages/index/login.html")
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if not su.login_data_is_valid(username, password):
            return render_template("pages/index/login.html")

        user = load_user(username)
        if not user:
            flash("Login unsuccessful. Please check your username and password.", "danger")
            return render_template("pages/index/login.html")
        if su.hash_password(password, user.salt) != user.password:
            flash("Login unsuccessful. Please check your username and password.", "danger")
            login_monitor = LoginMonitor.query.filter_by(user_id=user.id).first()
            login_monitor.update()
            return render_template("pages/index/login.html")
        login_user(user)

        user_agent = parse(request.headers.get('User-Agent'))
        last_login = user.last_login()
        current_login = LoginLog(user.id, user_agent)
        compare_logins(last_login, current_login, user)
        current_login.add_to_db()

        login_monitor = LoginMonitor.query.filter_by(user_id=user.id).first()
        if not login_monitor:
            login_monitor = LoginMonitor(user.id, date.today(), 0)
            login_monitor.add_to_db()
        if login_monitor.login_count >= 3:
            notification = Notification(user.id, NotificationType.FAILED_LOGINS, login_monitor=login_monitor)
            notification.add_to_db()
        login_monitor.reset()

        return redirect(url_for("home"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("pages/index/register.html")
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        second_password = request.form["password-repeat"]
        first_name, last_name = request.form["firstname"], request.form["lastname"]

        if not su.registration_data_is_valid(username, first_name, last_name, password, second_password):
            return render_template("pages/index/register.html")

        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "danger")
            return render_template("pages/index/register.html")

        user = User(username, first_name, last_name, password)
        user.add_to_db()
        login_user(user, duration=timedelta(hours=1))
        return render_template("pages/index/recovery_password.html", user=user, new_acount=True), 201


@app.route("/recover", methods=["GET", "POST"])
def recover():
    if request.method == "GET":
        return render_template("pages/index/recover_password.html")
    if request.method == "POST":
        username = request.form["username"]
        recovery_password = request.form["recovery-password"]
        new_password, repeat_new_password = request.form["new-password"], request.form["repeat-new-password"]
        if su.recovery_data_is_valid(username, recovery_password, new_password, repeat_new_password):
            return render_template("pages/index/recover_password.html")

        user = User.query.filter_by(username=username).first()
        if not user:
            flash("No such user.", "danger")
            return render_template("pages/index/recover_password.html")

        if user.recovery_password != recovery_password:
            flash("Incorrect recovery password.", "danger")
            return render_template("pages/index/recover_password.html")

        user.recover(new_password)
        login_user(user)
        return render_template("pages/index/recovery_password.html", user=user, new_account=False)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("hello_world"))


@app.route("/home", methods=["GET"])
@login_required
def home():
    loans = loans_given(current_user)
    debts = loans_taken(current_user)
    return render_template("pages/home/home.html", user=current_user, loans_given=loans, loans_taken=debts)


@app.route("/messages")
@login_required
def messages():
    messages = LoanMessage.query.filter_by(receiver_id=current_user.id, resolved=False).all()
    notifications = Notification.query.filter_by(receiver_id=current_user.id).all()
    return render_template("pages/home/messages.html", messages=messages, notifications=notifications)


@app.route("/new-loan", methods=["GET", "POST"])
@login_required
def new_loan():
    if request.method == "GET":
        return render_template("pages/home/new_loan.html")
    if request.method == "POST":
        lender = User.query.filter_by(username=request.form["lender"]).first()
        if not lender:
            flash("No such user.", "danger")
            return render_template("pages/home/new_loan.html")
        if not su.validate_new_loan(request.form["deadline"], request.form["amount"]):
            flash("Invalid loan data.", "danger")
            return render_template("pages/home/new_loan.html")

        deadline = datetime.strptime(request.form["deadline"], "%Y-%m-%d")
        loan = Loan(lender.id, current_user.id, request.form["amount"], deadline)
        loan.add_to_db()

        return redirect(url_for("home"))
    return redirect(url_for("home"))


@app.route("/new-loan/<int:id>", methods=["PATCH", "DELETE"])
@login_required
def accept_loan(id):
    message = LoanMessage.query.filter_by(id=id).first()
    if not message:
        flash("No such message.", "danger")
        return redirect(url_for("home"))
    loan = Loan.query.filter_by(id=message.loan_id).first()
    if not loan:
        flash("No such loan.", "danger")
        return redirect(url_for("home"))

    if request.method == "PATCH":
        loan.accept_request()
    else:
        loan.reject_request()

    message.resolve()
    return redirect(url_for("messages"))


@app.route("/loans")
@login_required
def loans():
    loans = get_all_loans(current_user)
    debts = get_all_debts(current_user)
    return render_template("pages/home/your_loans.html", loans=loans, debts=debts, current_date=date.today())


@app.route("/repay/<int:id>/", methods=["POST", "DELETE", "PATCH"])
@login_required
def repay_loan(id):
    if request.method == "POST":
        loan = Loan.query.filter_by(id=id).first()
        if not loan:
            flash("No such loan.", "danger")
            return redirect(url_for("loans"))

        loan.pay_back()
        return redirect(url_for("home"))

    message = LoanMessage.query.filter_by(id=id).first()
    if not message:
        flash("No such message.", "danger")
        return redirect(url_for("messages"))
    loan = Loan.query.filter_by(id=message.loan_id).first()
    if not loan:
        flash("No such loan.", "danger")
        return redirect(url_for("messages"))

    if request.method == "DELETE":
        loan.reject_repayment()
    if request.method == "PATCH":
        loan.confirm_repayment()

    message.resolve()
    return redirect(url_for("messages"))


@app.route("/other-loans", methods=["GET"])
@login_required
def other_loans():
    search_results = search_users()
    return render_template("pages/home/other_loans.html", users=search_results)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "GET":
        return render_template("pages/home/profile.html", user=current_user)
    if request.method == "POST":  # change password
        old_password = request.form["old-password"]
        new_password = request.form["new-password"]
        second_new_password = request.form["new-password-repeat"]

        if su.hash_password(old_password, current_user.salt) != current_user.password:
            flash("Wrong password", "error")
            return render_template("pages/home/profile.html", user=current_user)
        if not su.validate_password_change(new_password, second_new_password):
            return render_template("pages/home/profile.html", user=current_user)

        current_user.password = su.hash_password(new_password, current_user.salt)
        db.session.commit()
        flash("Password changed successfully.", "success")
        return render_template("pages/home/profile.html", user=current_user)
    return redirect(url_for("home"))


@app.route("/logs")
@login_required
def logs():
    logs = get_logs(current_user)
    return render_template("pages/home/logs.html", logs=logs)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
