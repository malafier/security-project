from flask import Flask, render_template
import sqlite3

app = Flask(__name__)
connection = sqlite3.connect('../db/project.db')


@app.route('/')
def hello_world():  # put application's code here
    return render_template('index.html')


if __name__ == '__main__':
    app.run()
