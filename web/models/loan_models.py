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


class NotificationType(Enum):
    REQUEST_ACCEPTED_BORROWER = "{full_name} ({username}) accepted your loan request for {amount}."
    REQUEST_ACCEPTED_LENDER = "You accepted {full_name} ({username}) loan request for {amount}."
    REQUEST_REJECTED_BORROWER = "{full_name} ({username}) rejected your loan request for {amount}."
    REQUEST_REJECTED_LENDER = "You rejected {full_name} ({username}) loan request for {amount}."
    REPAY_ACCEPTED_BORROWER = "{full_name} ({username}) accepted your repayment request for {amount}."
    REPAY_ACCEPTED_LENDER = "You accepted {full_name} ({username}) repayment request for {amount}."
    REPAY_REJECTED_BORROWER = "{full_name} ({username}) rejected your repayment request for {amount}."
    REPAY_REJECTED_LENDER = "You rejected {full_name} ({username}) repayment request for {amount}."
    # FAILED_LOGIN = "Someone tried to log in to your account 3 times, but failed."
    LOGIN_FROM_NEW_DEVICE = "Is that you? Someone logged in to your account from a new device. Previous index was from {device_brand} {device_model} ({os_family} {os_version})."
    LOGIN_FROM_NEW_BROWSER = "Is that you? Someone logged in to your account from a new browser. Previous index was from {browser_family} {browser_version} on {os_family} {os_version}."


class MessageType(Enum):
    NEW_LOAN = "{full_name} ({username}) wants to borrow {amount} from you, until {deadline}. Do you accept?"
    REPAYMENT = "{full_name} ({username}) claims to repay {amount} to you. Do you accept?"


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
        self.log_change()
        message = LoanMessage(self.id, self.lender_id, MessageType.NEW_LOAN)
        message.add_to_db()

    def accept_request(self):
        self.status = LoanStatus.NOT_PAYED.value
        self.commit()
        self.log_change()
        self.send_notification(NotificationType.REQUEST_ACCEPTED_BORROWER, NotificationType.REQUEST_ACCEPTED_LENDER)

    def reject_request(self):
        self.status = LoanStatus.CANCELED.value
        self.commit()
        self.log_change()
        self.send_notification(NotificationType.REQUEST_REJECTED_BORROWER, NotificationType.REQUEST_REJECTED_LENDER)

    def pay_back(self):
        self.status = LoanStatus.PENDING.value
        self.commit()
        self.log_change()
        message = LoanMessage(self.id, self.lender_id, MessageType.REPAYMENT)
        message.add_to_db()

    def confirm_pay_back(self):
        self.status = LoanStatus.PAYED.value
        self.commit()
        self.log_change()
        self.send_notification(NotificationType.REPAY_ACCEPTED_BORROWER, NotificationType.REPAY_ACCEPTED_LENDER)

    def reject_pay_back(self):
        self.status = LoanStatus.NOT_PAYED.value
        self.commit()
        self.log_change()
        self.send_notification(NotificationType.REPAY_REJECTED_BORROWER, NotificationType.REPAY_REJECTED_LENDER)

    def log_change(self):
        log = LoanLog(self.id, self.status)
        log.add_to_db()

    def send_notification(self, borrower_notification_type: NotificationType,
                          lender_notification_type: NotificationType):
        lender_notification = Notification(self.id, self.lender_id, borrower_notification_type)
        lender_notification.add_to_db()
        borrower_notification = Notification(self.id, self.borrower_id, lender_notification_type)
        borrower_notification.add_to_db()


class LoanMessage(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'), nullable=False)
    message = db.Column(db.String(), nullable=False)
    resolved = db.Column(db.Boolean, nullable=False, default=False)
    timestamp = db.Column(db.DateTime, nullable=False)

    def __init__(self, loan_id, receiver_id, message_type: MessageType):
        self.loan_id = loan_id
        self.receiver_id = receiver_id
        self.timestamp = datetime.now()

        loan = Loan.query.filter_by(id=loan_id).first()
        user = User.query.filter_by(id=loan.borrower_id).first()
        if message_type == MessageType.NEW_LOAN:
            self.message = message_type.value.format(full_name=user.first_name + " " + user.last_name,
                                                     username=user.username,
                                                     amount=loan.amount,
                                                     deadline=loan.deadline)
        else:
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
    status = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)

    def __init__(self, loan_id, status):
        self.loan_id = loan_id
        self.status = status
        self.timestamp = datetime.now()

    def add_to_db(self):
        db.session.add(self)
        db.session.commit()


class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.String(), nullable=False)
    seen = db.Column(db.Boolean, nullable=False, default=False)
    timestamp = db.Column(db.DateTime, nullable=False)

    def __init__(self, receiver_id, notification_type: NotificationType, loan_id=None, login_log=None):
        self.receiver_id = receiver_id
        self.timestamp = datetime.now()

        user = User.query.filter_by(id=receiver_id).first()
        loan = Loan.query.filter_by(id=loan_id).first()
        if notification_type in [NotificationType.REQUEST_ACCEPTED_BORROWER, NotificationType.REQUEST_REJECTED_LENDER,
                                 NotificationType.REQUEST_REJECTED_BORROWER, NotificationType.REQUEST_ACCEPTED_LENDER,
                                 NotificationType.REPAY_ACCEPTED_BORROWER, NotificationType.REPAY_ACCEPTED_LENDER,
                                 NotificationType.REPAY_REJECTED_BORROWER, NotificationType.REPAY_REJECTED_LENDER]:
            self.message = notification_type.value.format(full_name=user.first_name + " " + user.last_name,
                                                          username=user.username,
                                                          amount=loan.amount)
        # elif message_type == NotificationType.FAILED_LOGIN:
        #     self.message = message_type.value
        elif notification_type == NotificationType.LOGIN_FROM_NEW_DEVICE:
            self.message = notification_type.value.format(device_brand=login_log.device_brand,
                                                          device_model=login_log.device_model,
                                                          os_family=login_log.os_family,
                                                          os_version=login_log.os_version)
        elif notification_type == NotificationType.LOGIN_FROM_NEW_BROWSER:
            self.message = notification_type.value.format(browser_family=login_log.browser_family,
                                                          browser_version=login_log.browser_version,
                                                          os_family=login_log.os_family,
                                                          os_version=login_log.os_version)

    def add_to_db(self):
        db.session.add(self)
        db.session.commit()

    def mark_as_seen(self):
        self.seen = True
        db.session.commit()
