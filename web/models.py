import os
import secrets
from datetime import datetime
from string import ascii_letters, digits

import pyscrypt
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy(disable_autonaming=True)  # model_class=Base)

PEPPER = os.environ.get("PEPPER", "VERY_SECRET_AND_COMPLEX_PEPPER")


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(), unique=True, nullable=False)
    first_name = db.Column(db.String(), nullable=False)
    last_name = db.Column(db.String(), nullable=False)
    password = db.Column(db.String(), nullable=False)
    salt = db.Column(db.String(16), nullable=False)
    recovery_password = db.Column(db.String(), nullable=False)

    def __init__(self, username, first_name, last_name, password):
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.salt = secrets.token_hex(16)
        self.password = hash_password(password, self.salt)
        self.recovery_password = "".join([secrets.choice(ascii_letters + digits) for _ in range(16)])

    def get_id(self):
        return str(self.username)

    def add_to_db(self):
        db.session.add(self)
        db.session.commit()

    def loans_given(self):
        return Loan.query.filter_by(lender_id=self.id).all()

    def loans_taken(self):
        return Loan.query.filter_by(borrower_id=self.id).all()


class Loan(db.Model):
    __tablename__ = 'loans'
    id = db.Column(db.Integer, primary_key=True)
    lender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    borrower_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    deadline = db.Column(db.Date(), nullable=False)

    def __init__(self, lender_id, borrower_id, amount, deadline):
        self.lender_id = lender_id
        self.borrower_id = borrower_id
        self.amount = amount
        self.deadline = deadline

    def add_to_db(self):
        db.session.add(self)
        db.session.commit()


class LoanStatus(db.Model):
    __tablename__ = 'loan_satus'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)


class LoanLogs(db.Model):
    __tablename__ = 'loan_logs'
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'), nullable=False)
    status_id = db.Column(db.Integer, db.ForeignKey('loan_satus.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)

    def __init__(self, loan_id, status_id):
        self.loan_id = loan_id
        self.status_id = status_id
        self.timestamp = datetime.now()

    def add_to_db(self):
        db.session.add(self)
        db.session.commit()


def hash_password(password, salt):
    return bytes(pyscrypt.hash(bytes(password + PEPPER, "utf8"), bytes(salt, "utf8"), 2048, 8, 1, 128))
