from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

current_user = None
password_current_user = None


app = Flask(__name__)

db = SQLAlchemy()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db' 

app.config['SQLALCHEMY_BINDS'] = {} 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from models import User,Employee,Department

db.create_all()


@app.route('/')
def home_page():

    if current_user:
        is_autorized = True
    else:
        is_autorized = False
        
    return render_template('index.html',is_autorized=is_autorized)

@app.route('/login')
def login():

    users_query = User.query.all()
    users_list = [(str(users.id), users.name) for users in users_query]

    render_template('login.html',users_list=users_list)


    


@app.route('/logout')
def logout():
    pass



if __name__ == '__main__':
    app.run(debug=True)