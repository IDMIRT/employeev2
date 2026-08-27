from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

db = SQLAlchemy()

current_user = None
password_current_user = None

@app.route('/')
def home_page():

    if current_user:
        is_autorized = True
    else:
        is_autorized = False
        
    return render_template('index.html',is_autorized=is_autorized)

@app.route('/login')
def login():
    pass


@app.route('/logout')
def logout():
    pass



if __name__ == '__main__':
    app.run(debug=True)