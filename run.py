from flask import Flask, render_template,request
from flask_sqlalchemy import SQLAlchemy
from pathlib import Path
from services import auth_users


current_dir = Path(__file__).resolve().parent
current_user = None
password_current_user = None


app = Flask(__name__)

db = SQLAlchemy()
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db' 

# app.config['SQLALCHEMY_BINDS'] = {} 
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# from models import Employee,Department

# db.create_all()

# def create_app():
#     pass



@app.route('/')
def home_page():

    if current_user:
        is_autorized = True
    else:
        is_autorized = False
        
    return render_template('index.html',is_autorized=is_autorized)

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method=='GET':           
        users_list = auth_users(current_dir)
        if not users_list[0] == []:
            return render_template('login.html',users_list=users_list)            
        else:
            return render_template('error.html',name_error = users_list[1])
        
    # elif request.method=='POST': 


    


@app.route('/logout')
def logout():
    pass



if __name__ == '__main__':
    app.run(debug=True)