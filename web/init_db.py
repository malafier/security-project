import sqlite3


def initialise():
    connection = sqlite3.connect('../db/project.db')
    cursor = connection.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT NOT NULL UNIQUE,
        firstName TEXT NOT NULL,
        lastName TEXT NOT NULL, 
        password TEXT NOT NULL,
        salt TEXT NOT NULL,
        recoveryPassword TEXT NOT NULL 
    );""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS loans (
        id INTEGER PRIMARY KEY,
        lenderId INTEGER NOT NULL,
        borrowerId INTEGER NOT NULL,
        amount DECIMAL NOT NULL,
        deadline DATE NOT NULL,
        FOREIGN KEY (lenderId) REFERENCES user(id),
        FOREIGN KEY (borrowerId) REFERENCES user(id)
    );""")
