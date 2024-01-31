import math
import os
import re
from datetime import datetime
from string import ascii_letters, digits
from flask import flash

import pyscrypt


PEPPER = os.environ.get("PEPPER", "VERY_SECRET_AND_COMPLEX_PEPPER")
SPECIAL_CHARS = "!@#$%^&*()-_+=~`[]{}|:;\"'<>,.?/"
IS_DOCKER = os.environ.get("IS_DOCKER", "False")

if IS_DOCKER == "True":
    PASS_PATH = "/web/resources/500-worst-passwords.txt"
else:
    PASS_PATH = "./web/resources/500-worst-passwords.txt"


def hash_password(password, salt):
    return bytes(pyscrypt.hash(bytes(password + PEPPER, "utf8"), bytes(salt, "utf8"), 2048, 8, 1, 128))


def validate_username(username):
    valid_length = 3 <= len(username) <= 16
    return valid_length and valid_chars(username, ascii_letters + digits + "_")


def validate_name(name):
    valid_length = 2 <= len(name) <= 20
    return valid_length and re.match(r"^[A-ZŻŹĆĄŚĘŁÓŃ][a-zżźćńółęąś]+$", name)


def validate_last_name(last_name):
    valid_length = 2 <= len(last_name) <= 30
    return valid_length and re.match(r"^[A-ZŻŹĆĄŚĘŁÓŃ][a-zżźćńółęąś]+($|-[A-ZŻŹĆĄŚĘŁÓŃ][a-zżźćńółęąś]+$)", last_name)


def validate_password(password):
    valid_length = 8 <= len(password) <= 64
    chars_are_valid = valid_chars(password, ascii_letters + digits + SPECIAL_CHARS)
    at_least_one_digit = any(char.isdigit() for char in password)
    at_least_one_letter = any(char.isalpha() for char in password)
    at_least_one_special_char = any(char in SPECIAL_CHARS for char in password)

    return valid_length and chars_are_valid and at_least_one_digit and at_least_one_letter and at_least_one_special_char


def registration_data_is_valid(username, first_name, last_name, password, second_password):
    flag = True
    if not validate_username(username):
        flash("Username must be between 3 and 16 characters long and can only contain letters, digits and underscores.", "danger")
        flag = False
    if not validate_name(first_name):
        flash("First name must be between 2 and 20 characters long and can only contain letters.", "danger")
        flag = False
    if not validate_last_name(last_name):
        flash("Last name must be between 2 and 30 characters long and can only contain letters.", "danger")
        flag = False
    if not validate_password(password):
        flash("Password must be between 8 and 64 characters long and must contain at least one letter, one digit and one special character.", "danger")
        flag = False
    if password != second_password:
        flash("Passwords do not match.", "danger")
        flag = False
    if in_dictionary(password):
        flash("Password is too weak.", "danger")
        flag = False
    return flag


def recovery_data_is_valid(username, recovery_password, new_password, repeat_new_password):
    flag = True
    if not validate_username(username):
        flash("Username must be between 3 and 16 characters long and can only contain letters, digits and underscores.", "danger")
        flag = False
    if not valid_chars(recovery_password, ascii_letters + digits):
        flash("Recovery password must contain only letters and digits.", "danger")
        flag = False
    if not validate_password(new_password):
        flash("Password must be between 8 and 64 characters long and must contain at least one letter, one digit and one special character.", "danger")
        flag = False
    if new_password != repeat_new_password:
        flash("Passwords do not match.", "danger")
        flag = False
    if in_dictionary(new_password):
        flash("Password is too weak.", "danger")
        flag = False
    return flag


def login_data_is_valid(username, password):
    return validate_username(username) and validate_password(password)


def validate_new_loan(deadline, amount):
    try:
        date = datetime.strptime(deadline, "%Y-%m-%d")
        pattern = re.compile(r'^\d+(\.\d{1,2})?$')
        return date >= datetime.now() and pattern.match(amount) and float(amount) > 0
    except ValueError:
        return False


def validate_password_change(new_password, repeat_new_password):
    flag = True
    if not validate_password(new_password):
        flash("Password must be between 8 and 64 characters long and must contain at least one letter, one digit and one special character.", "danger")
        flag = False
    if new_password != repeat_new_password:
        flash("Passwords do not match.", "danger")
        flag = False
    if in_dictionary(new_password):
        flash("Password is too weak.", "danger")
        flag = False
    return flag


def valid_chars(input: str, legal_chars: str) -> bool:
    return all([char in legal_chars for char in input])


def in_dictionary(password):
    with open(PASS_PATH, "r") as f:
        for line in f:
            if password == line.strip():
                return True
    return False


def entropy(password):
    total_chars_count = len(ascii_letters + digits + SPECIAL_CHARS)
    password_length = len(password)
    return password_length * math.log2(total_chars_count)
