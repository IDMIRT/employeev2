from flask import Flask, render_template,request,redirect,url_for
from sqlalchemy import inspect, MetaData
from pathlib import Path
from services import auth_users,check_user,check_docker,start_docker,stop_docker
from models import db,Employee,Department

# database_open = False
current_dir = Path(__file__).resolve().parent
current_user = None
password_current_user = None


app = Flask(__name__)

# db = SQLAlchemy()

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' #заглушка без неё init_app падает
db.init_app(app)

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
            with app.app_context():
                
                app.config['SQLALCHEMY_DATABASE_URI'] = dsn                
                db.engines[None] = db.create_engine(app.config['SQLALCHEMY_DATABASE_URI'], future=True)
                db.session.remove()
                db.engine.dispose()
               
                
                metadata = inspect(db.engine) 
                if not metadata.has_table(Employee.__tablename__):
                    print(f"Таблица '{Employee.__tablename__}' не найдена. Создаем структуру БД...") 
                    try: 
                        db.create_all() 
                        print("Таблицы Employee и Department созданы успешно.") 
                    except Exception as e: 
                        error_message = f"Ошибка создания таблиц: {str(e)}" 
                else: print("Структура БД уже существует.")
           
            

    return redirect(url_for('home_page'))
    


@app.route('/logout',methods=['GET', 'POST'])
def logout():
    stopped_db = stop_docker()

    if stopped_db == True:
        current_user = None
        
    
    return redirect(url_for('home_page')) 


if __name__ == '__main__':
    app.run(debug=True)