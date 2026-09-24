from flask import Flask, render_template,request,redirect,url_for,session,flash
from sqlalchemy import inspect, MetaData, text,func
from pathlib import Path
from services import auth_users,check_user,check_docker,start_docker,stop_docker
from models import db,Employee,Department
import secrets # на сессиях зависают secret_key в куках, потому просто генерим secret_key
import sys
import os
from sqlalchemy.orm import selectinload 

current_dir = Path(__file__).resolve().parent

app = Flask(__name__)
#дабы не сбрасывать куки буду менять ключ
app.secret_key = secrets.token_urlsafe(32)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' #заглушка обязательна, без неё init_app падает
db.init_app(app)

@app.context_processor 
def user_autorized(): 
    return dict(is_authorized=bool(session.get('user')))

@app.route('/')
def home_page():
    
    return render_template('index.html')    
    


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
        user_password = request.form.get("password")
        
        
        user_db = check_user(user_id,user_password,current_dir)
        if user_db[0] == True:            
            session['user'] = user_db[1] 
            session.modified = True
            dsn = start_docker()

        if check_docker() != True:            
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


@app.route('/search', methods=['GET'])
def search():    
    return render_template('search.html', search_query="")


@app.route('/employees',methods=['GET', 'POST'])
def employees(): 
    current_page = request.args.get('page',1, type=int)
    sorting = request.args.get('sort','name')
    order = request.args.get('order','asc')

    page_count = 50
    search_query = request.args.get('str_search', '').strip()    
    employees_query = Employee.query.join(Department)

    if search_query: 
        search_string = f'%{search_query.lower()}%' 
        employees_query = employees_query.filter(func.lower(Employee.name).like(search_string))

    #из за ограничений ORM идею пришлось отбросить Employee.department.name_department :(
    # sort_dict = {'name':Employee.name,'employee_position':Employee.employee_position,
    #              'salary':Employee.salary,'employment_date':Employee.date_employment,
    #              'department': Employee.department.name_department} 

    
    sort_columns = {'name': 'employee.name', 'employee_position': 'employee.employee_position', 
                    'salary': 'employee.salary', 'date_employment': 'employee.date_employment', 
                    'department': 'department.name_department'} 
    
    column_name = sort_columns.get(sorting, 'employee.name') 
    sort_field = text(f"{column_name} {order}") 
    employees_query = employees_query.order_by(sort_field) 

    pagination = employees_query.paginate(page=current_page, per_page=page_count, error_out=False) 

    return render_template('employees.html', 
                           employees=pagination.items, 
                           pagination=pagination, 
                           current_sort=sorting, 
                           current_order=order)


@app.route('/employee/edit/<int:emp_id>', methods=['GET', 'POST'])
def edit_employee(emp_id):
    employee = db.session.query(Employee).options(selectinload(Employee.department)).get(emp_id)
    
    if not employee:
        flash('Сотрудник не найден!', 'danger')
        return redirect(url_for('employees'))

    if request.method == 'POST':
        new_dept_id = request.form.get('department_select')
        
        if not new_dept_id or new_dept_id == "":
            flash('Ошибка: Отдел не выбран.', 'warning')
        else:
            employee.department_id = int(new_dept_id)
            
            if employee.boss_department == True:
                employee.boss_department = False 
            
            db.session.commit()
            flash(f'Подразделение успешно изменено на {new_dept_id}', 'success')
            
        return redirect(url_for('edit_employee', emp_id=emp_id))

    all_departments = Department.query.order_by(Department.name_department.asc()).all()
    
    current_boss_dept = db.session.query(Employee.name)\
    .filter(Employee.department_id == employee.department_id, Employee.boss_department == True).scalar()
        
    return render_template('edit_employee.html', 
                           employee=employee, 
                           departments=all_departments,
                           current_boss=current_boss_dept)


@app.route('/departments',methods=['GET', 'POST'])
def departments():
    #в orm реализация этого запроса очень заморочена, потом разобраться
    text_sql = """select dep.id, dep.name_department, 
    parent.name_department as parent_department, 
    emp.name as boss_dept 
    from department as dep 
    left join department as parent on dep.parent_id=parent.id
    left join (select name,department_id, boss_department from employee where boss_department=True) as emp 
    on dep.id=emp.department_id"""
    
    dict_department = db.session.execute(text(text_sql)).mappings().all()

    return render_template("departments.html",departments=dict_department)


@app.route('/department/edit/<int:dept_id>', methods=['GET', 'POST']) 
def edit_department(dept_id): 

    dept = db.session.query(Department).get(int(dept_id)) 
    if not dept: 
        flash('Отдел не найден!', 'danger') 
        return redirect(url_for('departments')) 
        

    if request.method == 'POST': 
        new_boss_name = request.form.get('boss_select')
        
        db.session.query(Employee).filter(
            Employee.department_id == dept_id, 
            Employee.boss_department == True
        ).update({Employee.boss_department: False})
        
        if new_boss_name:
            new_boss = db.session.query(Employee).filter(
                Employee.name == new_boss_name, 
                Employee.department_id == dept_id
            ).first() 
            
            if not new_boss: 
                flash(f'Ошибка: Сотрудник {new_boss_name} не состоит в этом отделе.', 'danger') 
            else:
                new_boss.boss_department = True 
                db.session.commit() 
                flash('Руководитель успешно изменен!', 'success')
                
        return redirect(url_for('edit_department', dept_id=dept_id)) 

    department_employees = db.session.query(Employee.id, Employee.name)\
        .filter(Employee.department_id == dept_id)\
        .order_by(Employee.name.asc()).all() 
        
    current_boss_name = db.session.query(Employee.name)\
        .filter(Employee.department_id == dept_id, Employee.boss_department == True)\
        .scalar() 
        
    return render_template(
        'edit_department.html', 
        department=dept, 
        employees=department_employees,          
        current_boss=current_boss_name           
    )


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


    