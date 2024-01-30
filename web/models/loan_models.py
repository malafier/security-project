from datetime import datetime
from enum import Enum

from web.models.db_init import db
from web.models.user_models import User


class LoanStatus(Enum):
    REQUEST_IN_PROGRESS = 1
    NOT_PAYED = 2
    PENDING = 3
    PAYED = 4
    CANCELED = 5


class MessageType(Enum):
    NEW_LOAN = "{full_name} ({username}) wants to borrow {amount} from you, until {deadline}. Do you accept?"
    REPAYMENT = "{full_name} ({username}) claims to repay {amount} to you. Do you accept?"


class LoanLogType(Enum):
    REQUEST = "{req_full_name} ({req_username}) asked {res_full_name} ({res_username}) for a loan for {amount} until {deadline}."
    REQUEST_ACCEPTED = "{res_full_name} ({res_username}) accepted {req_full_name} ({req_username}) loan request for {amount} until {deadline}."
    REQUEST_REJECTED = "{res_full_name} ({res_username}) rejected {req_full_name} ({req_username}) loan request for {amount} until {deadline}."
    REPAY = "{req_full_name} ({req_username}) claims to repay {amount} to {res_full_name} ({res_username})."
    REPAY_ACCEPTED = "{res_full_name} ({res_username}) accepted {req_full_name} ({req_username}) repayment request for {amount}."
    REPAY_REJECTED = "{res_full_name} ({res_username}) rejected {req_full_name} ({req_username}) repayment request for {amount}."


class Loan(db.Model):
    __tablename__ = 'loans'
    id = db.Column(db.Integer, primary_key=True)
    lender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    borrower_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    deadline = db.Column(db.Date(), nullable=False)
    status = db.Column(db.Integer, nullable=False)

    def __init__(self, lender_id, borrower_id, amount, deadline):
        self.lender_id = lender_id
        self.borrower_id = borrower_id
        self.amount = amount
        self.deadline = deadline
        self.status = LoanStatus.REQUEST_IN_PROGRESS.value

    def add_to_db(self):
        db.session.add(self)
        db.session.commit()
        self.log_change(LoanLogType.REQUEST)
        message = LoanMessage(self.id, self.lender_id, MessageType.NEW_LOAN)
        message.add_to_db()

    def accept_request(self):
        self.status = LoanStatus.NOT_PAYED.value
        db.session.commit()
        self.log_change(LoanLogType.REQUEST_ACCEPTED)

    def reject_request(self):
        self.status = LoanStatus.CANCELED.value
        db.session.commit()
        self.log_change(LoanLogType.REQUEST_REJECTED)

    def pay_back(self):
        self.status = LoanStatus.PENDING.value
        db.session.commit()
        self.log_change(LoanLogType.REPAY)
        message = LoanMessage(self.id, self.lender_id, MessageType.REPAYMENT)
        message.add_to_db()

    def confirm_repayment(self):
        self.status = LoanStatus.PAYED.value
        db.session.commit()
        self.log_change(LoanLogType.REPAY_ACCEPTED)

    def reject_repayment(self):
        self.status = LoanStatus.NOT_PAYED.value
        db.session.commit()
        self.log_change(LoanLogType.REPAY_REJECTED)

    def log_change(self, log_type: LoanLogType):
        log = LoanLog(self.id, self.status, log_type)
        log.add_to_db()


class LoanMessage(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'), nullable=False)
    message = db.Column(db.String(), nullable=False)
    resolved = db.Column(db.Boolean, nullable=False, default=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    new_loan = db.Column(db.Boolean, nullable=False, default=True)

    def __init__(self, loan_id, receiver_id, message_type: MessageType):
        self.loan_id = loan_id
        self.receiver_id = receiver_id
        self.timestamp = datetime.now()

        loan = Loan.query.filter_by(id=loan_id).first()
        user = User.query.filter_by(id=loan.borrower_id).first()
        if message_type == MessageType.NEW_LOAN:
            self.new_loan = True
            self.message = message_type.value.format(full_name=user.first_name + " " + user.last_name,
                                                     username=user.username,
                                                     amount=loan.amount,
                                                     deadline=loan.deadline)
        else:
            self.new_loan = False
            self.message = message_type.value.format(full_name=user.first_name + " " + user.last_name,
                                                     username=user.username,
                                                     amount=loan.amount)

    def add_to_db(self):
        db.session.add(self)
        db.session.commit()

    def resolve(self):
        self.resolved = True
        db.session.commit()


class LoanLog(db.Model):
    __tablename__ = 'loan_logs'
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'), nullable=False)
    message = db.Column(db.String(), nullable=False)
    status = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)

    def __init__(self, loan_id, status, log_type: LoanLogType):
        self.loan_id = loan_id
        self.status = status
        self.timestamp = datetime.now()

        loan = Loan.query.filter_by(id=loan_id).first()
        lender = User.query.filter_by(id=loan.lender_id).first()
        borrower = User.query.filter_by(id=loan.borrower_id).first()
        if log_type in [LoanLogType.REQUEST, LoanLogType.REQUEST_ACCEPTED, LoanLogType.REQUEST_REJECTED]:
            self.message = log_type.value.format(req_full_name=borrower.first_name + " " + borrower.last_name,
                                                 req_username=borrower.username,
                                                 res_full_name=lender.first_name + " " + lender.last_name,
                                                 res_username=lender.username,
                                                 amount=loan.amount,
                                                 deadline=loan.deadline)
        else:
            self.message = log_type.value.format(req_full_name=borrower.first_name + " " + borrower.last_name,
                                                 req_username=borrower.username,
                                                 res_full_name=lender.first_name + " " + lender.last_name,
                                                 res_username=lender.username,
                                                 amount=loan.amount)

    def add_to_db(self):
        db.session.add(self)
        db.session.commit()
