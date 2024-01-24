import secrets
from datetime import datetime
from string import ascii_letters, digits

from flask_login import UserMixin
from web.models.db_init import db
from web.security_utils import hash_password


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

    def last_login(self):
        return LoginLog.query.filter_by(user_id=self.id).order_by(LoginLog.timestamp.desc()).first()


class LoginLog(db.Model):
    __tablename__ = 'login_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    browser_family = db.Column(db.String(), nullable=False)
    browser_version = db.Column(db.String(), nullable=False)
    os_family = db.Column(db.String(), nullable=False)
    os_version = db.Column(db.String(), nullable=False)
    device_family = db.Column(db.String(), nullable=False)
    device_brand = db.Column(db.String(), nullable=False)
    device_model = db.Column(db.String(), nullable=False)
    is_mobile = db.Column(db.Boolean, nullable=False)
    is_tablet = db.Column(db.Boolean, nullable=False)
    is_pc = db.Column(db.Boolean, nullable=False)
    is_bot = db.Column(db.Boolean, nullable=False)

    def __init__(self, user_id, user_info):
        self.user_id = user_id
        self.timestamp = datetime.now()
        self.browser_family = user_info.browser.family
        self.browser_version = user_info.browser.version_string
        self.os_family = user_info.os.family
        self.os_version = user_info.os.version_string
        self.device_family = user_info.device.family if user_info.device.family else "N/A"
        self.device_brand = user_info.device.brand if user_info.device.brand else "N/A"
        self.device_model = user_info.device.model if user_info.device.model else "N/A"
        self.is_mobile = user_info.is_mobile
        self.is_tablet = user_info.is_tablet
        self.is_pc = user_info.is_pc
        self.is_bot = user_info.is_bot

    def add_to_db(self):
        db.session.add(self)
        db.session.commit()