from datetime import datetime
from enum import Enum

from models.db_init import db


class NotificationType(Enum):
    FAILED_LOGINS = "Someone tried to log in to your account {tries} times unsuccessfully."
    LOGIN_FROM_NEW_DEVICE = "Is that you? Someone logged in to your account from a new device. Previous index was from {device_brand} {device_model} ({os_family} {os_version})."
    LOGIN_FROM_NEW_BROWSER = "Is that you? Someone logged in to your account from a new browser. Previous index was from {browser_family} {browser_version} on {os_family} {os_version}."


class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.String(), nullable=False)
    # seen = db.Column(db.Boolean, nullable=False, default=False)
    timestamp = db.Column(db.DateTime, nullable=False)

    def __init__(self, receiver_id, notification_type: NotificationType, login_log=None, login_monitor=None):
        self.receiver_id = receiver_id
        self.timestamp = datetime.now()

        if notification_type == NotificationType.FAILED_LOGINS:
            self.message = notification_type.value.format(tries=login_monitor.login_count)
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

    # def mark_as_seen(self):
    #     self.seen = True
    #     db.session.commit()
