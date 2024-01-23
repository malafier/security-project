import os
import re
from datetime import datetime
from string import ascii_letters, digits

import pyscrypt


PEPPER = os.environ.get("PEPPER", "VERY_SECRET_AND_COMPLEX_PEPPER")
SPECIAL_CHARS = "!@#$%^&*()-_+=~`[]{}|:;\"'<>,.?/"

def hash_password(password, salt):
    return bytes(pyscrypt.hash(bytes(password + PEPPER, "utf8"), bytes(salt, "utf8"), 2048, 8, 1, 128))


def validate_username(username):
    valid_length = 3 <= len(username) <= 16
    return valid_length and valid_chars(username, ascii_letters + digits + "_")


def validate_name(name):
    valid_length = 2 <= len(name) <= 20
    return valid_length and re.match(r"^[A-Z][a-z]+$", name)


def validate_last_name(last_name):
    valid_length = 2 <= len(last_name) <= 30
    return valid_length and re.match(r"^[A-Z][a-z]+($|-[A-Z][a-z]+$)", last_name)


def validate_password(password):
    valid_length = 8 <= len(password) <= 64
    chars_are_valid = valid_chars(password, ascii_letters + digits + SPECIAL_CHARS)
    at_least_one_digit = any(char.isdigit() for char in password)
    at_least_one_letter = any(char.isalpha() for char in password)
    at_least_one_special_char = any(char in SPECIAL_CHARS for char in password)

    return valid_length and chars_are_valid and at_least_one_digit and at_least_one_letter and at_least_one_special_char


def registration_data_is_valid(username, first_name, last_name, password, second_password):
    return validate_username(username) and validate_name(first_name) and validate_last_name(last_name) \
        and validate_password(password) and password == second_password


def login_data_is_valid(username, password):
    return validate_username(username) and validate_password(password)


def validate_deadline_date(deadline):
    try:
        date = datetime.strptime(deadline, "%Y-%m-%d")
        return date >= datetime.now()
    except ValueError:
        return False


def valid_chars(input: str, legal_chars: str) -> bool:
    return all([char in legal_chars for char in input])


def in_dictionary(password):
    with open("./resources/500-worst-passwords.txt", "r") as f:
        for line in f:
            if password == line.strip():
                return True
    return False
