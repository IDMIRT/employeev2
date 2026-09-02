from flask import Flask, render_template,request,redirect,url_for
from flask_sqlalchemy import SQLAlchemy
from pathlib import Path
from services import auth_users,check_user,check_docker,start_docker,stop_docker

database_open = False
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
        user_id = int(request.form.get("username"))
        password_current_user=request.form.get("password")
        

        user_db = check_user(user_id,password_current_user,current_dir)
        if user_db[0] == True and check_docker()==True:
            current_user = user_db[1] 
            dsn = start_docker()

        if not dsn == None:
            app.config['SQLALCHEMY_DATABASE_URI'] = dsn 
            # app.config['SQLALCHEMY_BINDS'] = {} 
            app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

            if database_open==False :
                from models import Employee,Department
                with app.app_context():
                    db.create_all()

    return redirect(url_for('home_page'))
    


@app.route('/logout',methods=['GET', 'POST'])
def logout():
    stopped_db = stop_docker()

    if stopped_db == True:
        current_user = None
        
    
    return redirect(url_for('home_page')) 


if __name__ == '__main__':
    app.run(debug=True)