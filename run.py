from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

db = SQLAlchemy()

@app.route('/')
def home_page():
    return render_template('index.html')

@app.route('/login')
def login():
    pass



if __name__ == '__main__':
    app.run(debug=True)