from flask import Flask, render_template,request,redirect,url_for,session,flash
from sqlalchemy import inspect, MetaData
from pathlib import Path
from services import auth_users,check_user,check_docker,start_docker,stop_docker
from models import db,Employee,Department

# database_open = False
current_dir = Path(__file__).resolve().parent
current_user = None
password_current_user = None


app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' #заглушка без неё init_app падает
db.init_app(app)


@app.route('/')
def home_page():

    if session.get('user',None):
        is_autorized = True
    else:
        is_autorized = False
        
    return render_template('index.html',is_autorized=is_autorized)


@app.route('/error')
def error(message_error=None):
    
    return render_template('error.html', name_error=message_error)

    

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
        if user_db[0] == True:
            # current_user = user_db[1] 
            session['user'] = user_db[1] 
            dsn = start_docker()

        if check_docker()[0] == False:
            # flash(f"Ошибка, нет установленного Docker: {str(e)}", "danger")
            return redirect(url_for('error'),f"Ошибка, нет установленного Docker: {str(e)}")

        if not dsn == None:
            with app.app_context():
                
                app.config['SQLALCHEMY_DATABASE_URI'] = dsn #нельзя просто поменять uri нужно полностью все сбросить               
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
                        error_message = f"Ошибка создания таблиц: {e}" 
                else: 
                    print("Структура БД уже существует.")
        
           
            

    return redirect(url_for('home_page'))
    


@app.route('/logout',methods=['GET', 'POST'])
def logout():
    stopped_db = stop_docker()

    if stopped_db == True:
        session['user'] = None
        
    
    return redirect(url_for('home_page')) 


if __name__ == '__main__':

    docker_install = check_docker() #если нет установленного докер то нет смысла запускать

    if len(docker_install) == 1:
        app.run(debug=True)
    else:
        print(docker_install[1])


    # if check_docker()==True:
        
    # else:
    #     print("Оши")