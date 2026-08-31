from flask import Flask, render_template,request
from flask_sqlalchemy import SQLAlchemy
from pathlib import Path
from services import auth_users,check_user,check_docker,start_docker


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

    error_message = None

    if request.method=='GET':           
        users_list = auth_users(current_dir)
        if not users_list[0] == []:
            return render_template('login.html',users_list=users_list)            
        else:
            return render_template('error.html',name_error = users_list[1])
        
    elif request.method=='POST': 
        current_user = request.form.get("username")
        password_current_user=request.form.get("password")

        check = check_user(current_user,password_current_user,current_dir)
        if check == True and check_docker()==True:
            dsn = start_docker(current_user,password_current_user)

        if not dsn == None:
            app.config['SQLALCHEMY_DATABASE_URI'] = dsn 
            # app.config['SQLALCHEMY_BINDS'] = {} 
            app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

            from models import Employee,Department
            with app.app_context():
                db.create_all()




            
            



         



    


@app.route('/logout')
def logout():
    pass



if __name__ == '__main__':
    app.run(debug=True)