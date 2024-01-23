from sqlalchemy import func

from web.models.db_init import db
from web.models.user_models import User, LoginLog
from web.models.loan_models import Loan, LoanStatus, Notification, NotificationType


def loans_given(user: User):
    query = (
        db.session.query(User.username, func.sum(Loan.amount).label('total_amount'))
        .join(Loan, User.id == Loan.borrower_id)
        .filter(Loan.lender_id == user.id, Loan.status.in_([LoanStatus.NOT_PAYED.value, LoanStatus.PENDING.value]))
        .group_by(User.username)
    )
    return query.all()


def loans_taken(user: User):
    query = (
        db.session.query(User.username, func.sum(Loan.amount).label('total_amount'))
        .join(Loan, User.id == Loan.lender_id)
        .filter(Loan.borrower_id == user.id,
                Loan.status.in_([LoanStatus.NOT_PAYED.value, LoanStatus.PENDING.value]))
        .group_by(User.username)
    )
    return query.all()


def search_users(search_string):
    query = (
        db.session.query(
            User.username,
            func.concat(User.first_name, ' ', User.last_name).label('full_name'),
            func.sum(
                db.case(
                    [
                        (Loan.status.in_([LoanStatus.NOT_PAYED.value, LoanStatus.PENDING.value]),
                         db.case([(Loan.deadline >= func.current_date(), Loan.amount)], else_=0))
                    ],
                    else_=0
                )
            ).label('green_debt'),
            func.sum(
                db.case(
                    [
                        (Loan.status.in_([LoanStatus.NOT_PAYED.value, LoanStatus.PENDING.value]),
                         db.case([(Loan.deadline < func.current_date(), Loan.amount)], else_=0))
                    ],
                    else_=0
                )
            ).label('red_debt')
        )
        .join(Loan, User.id == Loan.borrower_id)
        .filter(User.username.like(f"%{search_string}%"))
        .filter(Loan.status.in_([LoanStatus.NOT_PAYED.value, LoanStatus.PENDING.value]),
                Loan.deadline > func.current_date())
        .group_by(User.id)
    )
    return query.all()


def get_all_loans(user: User):
    loans = Loan.query.filter(
        Loan.lender_id == user.id,
        Loan.status.in_([LoanStatus.NOT_PAYED.value, LoanStatus.PENDING.value, LoanStatus.PAYED.value])
    ).all()

    return loans


def get_all_debts(user: User):
    debts = Loan.query.filter(
        Loan.borrower_id == user.id,
        Loan.status.in_([LoanStatus.NOT_PAYED.value, LoanStatus.PENDING.value, LoanStatus.PAYED.value])
    ).all()

    return debts


def compare_logins(previous_login: LoginLog, current_login: LoginLog, user: User):
    if previous_login is None:
        return

    if previous_login.device_family != current_login.device_family or \
            previous_login.device_brand != current_login.device_brand or \
            previous_login.device_model != current_login.device_model or \
            previous_login.is_mobile != current_login.is_mobile or \
            previous_login.is_tablet != current_login.is_tablet or \
            previous_login.is_pc != current_login.is_pc or \
            previous_login.is_bot != current_login.is_bot:
        notification = Notification(user.id, NotificationType.LOGIN_FROM_NEW_DEVICE, login_log=previous_login)
        notification.add_to_db()
        return

    if previous_login.browser_family != current_login.browser_family or \
            previous_login.browser_version != current_login.browser_version or \
            previous_login.os_family != current_login.os_family or \
            previous_login.os_version != current_login.os_version:
        notification = Notification(user.id, NotificationType.LOGIN_FROM_NEW_BROWSER, login_log=previous_login)
        notification.add_to_db()
    return

