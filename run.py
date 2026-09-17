from flask import Flask, render_template,request,redirect,url_for,session,flash
from sqlalchemy import inspect, MetaData
from pathlib import Path
from services import auth_users,check_user,check_docker,start_docker,stop_docker
from models import db,Employee,Department
import secrets # на сессиях зависают secret_key в куках, потому просто генерим secret_key
import sys
import os

current_dir = Path(__file__).resolve().parent
# current_user = None
# password_current_user = None


app = Flask(__name__)
#дабы не сбрасывать куки менять ключ
app.secret_key = secrets.token_urlsafe(32)
# сессии
# app.config['TEMPLATES_AUTO_RELOAD'] = True
# app.jinja_env.auto_reload = True
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# сессии
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' #заглушка обязательна, без неё init_app падает
db.init_app(app)

# @app.context_processor 
# def navbar_visible(): 
#     return dict(is_authorized=bool(session.get('user')))

@app.route('/')
def home_page():

    if session.get('user',None):
        is_authorized = True
    else:
        is_authorized = False
        
    return render_template('index.html',is_authorized=is_authorized)


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
        session['password']=request.form.get("password")
        

        user_db = check_user(user_id,session['password'],current_dir)
        if user_db[0] == True:            
            session['user'] = user_db[1] 
            # session.modified = True
            dsn = start_docker()

        if check_docker() != True:
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

@app.route('/employees',methods=['GET', 'POST'])
def employees(): 
    current_page = request.args.get('page',1)
    sorting = request.args.get('sort','name')
    order = request.args.get('order','asc')

    page_count = 50

    employees_query = Employee.query.order_by(Employee.id.asc)

    sort_dict = {'name':Employee.name,'employee_position':Employee.employee_position,
                 'salary':Employee.salary,'employment_date':Employee.date_employment}

    field = sort_dict.get(sorting,Employee.name)

    order_dict = {'asc':field.asc(),'desc':field.desc()}
    employees_query = employees_query.order_by(order_dict.get(order,field.asc())) 

    pagination = employees_query.paginate(page=current_page, per_page=page_count, error_out=False) 
    employees = pagination.items # Список объектов сотрудников только для текущей страницы

    return render_template('employees.html', 
                           employees=pagination.items, 
                           pagination=pagination, 
                           current_sort=sorting, 
                           current_order=order)
    


@app.route('/logout',methods=['GET', 'POST'])
def logout():
    stopped_db = stop_docker()

    if stopped_db == True:
        session['user'] = None           
    
    return redirect(url_for('home_page')) 



if __name__ == '__main__':

    docker_installing = check_docker() #если нет установленного докер то нет смысла запускать

    if docker_installing == True:
        app.run(debug=True)
    else:
        print(docker_installing[1])


    # if check_docker()==True:
        
    # else:
    #     print("Ошибка работы c Docker")