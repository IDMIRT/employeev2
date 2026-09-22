from flask import Flask, render_template,request,redirect,url_for,session,flash
from sqlalchemy import inspect, MetaData, text
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

@app.context_processor 
def user_autorized(): 
    return dict(is_authorized=bool(session.get('user')))

@app.route('/')
def home_page():

    # if session.get('user',None):
    #     is_authorized = True
    # else:
    #     is_authorized = False
    return render_template('index.html')    
    # return render_template('index.html',is_authorized=is_authorized)


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
        # session['password']=request.form.get("password")
        user_password = request.form.get("password")
        

        # user_db = check_user(user_id,session['password'],current_dir)
        user_db = check_user(user_id,user_password,current_dir)
        if user_db[0] == True:            
            session['user'] = user_db[1] 
            session.modified = True
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
    current_page = request.args.get('page',1, type=int)
    sorting = request.args.get('sort','name')
    order = request.args.get('order','asc')

    page_count = 50

    # employees_query = Employee.query.order_by(Employee.id.asc)
    employees_query = Employee.query.join(Department)

    sort_dict = {'name':Employee.name,'employee_position':Employee.employee_position,
                 'salary':Employee.salary,'employment_date':Employee.date_employment}

    field = sort_dict.get(sorting,Employee.name)

    # order_dict = {'asc':field.asc(),'desc':field.desc()}
    if order == 'desc':
        # employees_query = employees_query.join(Department).order_by(field.desc()) 
        employees_query = employees_query.order_by(field.desc()) 
    else:
        employees_query = employees_query.order_by(field.asc()) 
        # employees_query = employees_query.order_by(order_dict.get(order,field.asc())) 

    pagination = employees_query.paginate(page=current_page, per_page=page_count, error_out=False) 
    employees = pagination.items # Список объектов сотрудников только для текущей страницы

    return render_template('employees2.html', 
                           employees=pagination.items, 
                           pagination=pagination, 
                           current_sort=sorting, 
                           current_order=order)


@app.route('/departments',methods=['GET', 'POST'])
def departments():
    #в orm реализация этого запроса очень заморочена, потом разобраться
    text_sql = """select dep.name_department, 
    parent.name_department as parent_department, 
    emp.name as boss_dept 
    from department as dep 
    left join department as parent on dep.parent_id=parent.id
    left join (select name,department_id, boss_department from employee where boss_department=True) as emp 
    on dep.id=emp.department_id"""

    # dep_cursor = db.session.execute(text(text_sql)).fetchall()
    dict_department = db.session.execute(text(text_sql)).mappings().all()

    return render_template("departments.html",departments=dict_department)


@app.route('/department/edit/<int:dept_id>', methods=['GET', 'POST']) 
def edit_department(dept_id): 
    # Получаем объект отдела по ID из базы 
    dept = db.session.query(Department).get(int(dept_id)) 
    if not dept: 
        flash('Отдел не найден!', 'danger') 
        return redirect(url_for('departments')) 
# Если пришла форма с данными (нажали кнопку Сохранить) 
    if request.method == 'POST': 
        new_boss_name = request.form.get('boss_select') 
        # Сначала снимаем статус "Босс" со всех сотрудников этого отдела 
        db.session.query(Employee).filter(Employee.department_id == dept_id, Employee.boss_department == True).update({Employee.boss_department: False}) 
        # Затем ищем выбранного сотрудника и назначаем его боссом 
        new_boss = db.session.query(Employee).filter(Employee.name == new_boss_name, Employee.department_id == dept_id).first() 
        if not new_boss: 
            flash(f'Ошибка: Сотрудник {new_boss_name} не состоит в этом отделе.', 'danger') 
        else: new_boss.boss_department = True 
        db.session.commit() 
        flash('Руководитель успешно изменен!', 'success') 
        # Перезагружаем ту же страницу, чтобы увидеть изменения 
        return redirect(url_for('edit_department', dept_id=dept_id)) 
    # --- Подготовка данных для отображения формы --- 
    # # Список ТОЛЬКО сотрудников ЭТОГО отдела для выпадающего списка 
    employees_in_dept = db.session.query(Employee.id, Employee.name).filter(Employee.department_id == dept_id).order_by(Employee.name.asc()).all() 
    # Имя текущего начальника (если есть) 
    current_boss = db.session.query(Employee.name).filter(Employee.department_id == dept_id, Employee.boss_department == True).scalar() 
    return render_template('edit_department.html', department=dept, employees=employees_in_dept, current_boss=current_boss)


    


# @app.route('/search',methods=['GET', 'POST'])
# def search():
#     pass



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