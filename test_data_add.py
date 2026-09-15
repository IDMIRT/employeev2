import os
import time
from pathlib import Path
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from services import start_docker, stop_docker 
from models import db, Employee, Department
from mimesis import Person
from mimesis.locales import Locale
import random
import argparse

def generate_data(dsn=None, count_employees=5000, count_department=10): 
    """
    Функция генерации данных
    dsn - строка подключения
    count_employees - количество тестовых сотрудников
    count_department - количество подразделений в организации
    """
    print(f"Подключение к целевой БД: {dsn}")

    if not dsn: #потом сделать загрузку из env
        dsn = 'postgresql+psycopg2://employee:employee@localhost:5432/employees'
    
    engine = create_engine(dsn, echo=False, future=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_session = SessionLocal()

    inspector = inspect(engine)
    
    if not inspector.has_table(Employee.__tablename__):
        print("Таблицы отсутствуют. Инициализируем структуру...")
        db.metadata.create_all(bind=engine)
    else:
        print("Очистка старых данных...")
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM employee"))
            conn.execute(text("DELETE FROM department"))
            
    person = Person(Locale.RU)
   
    
    t_start = time.time()
    
    # Верхний уровень - организация
    root_dept = Department(name_department="ООО 'Рога и копыта'")
    db_session.add(root_dept)
    db_session.commit() 
    choice_department = [root_dept]

    #для увеличения уровней вложенности можно просто увеличить количество отделов random раскидает
    for i in range(count_department): 
        parent_choice = random.choice(choice_department) 
        dept = Department(name_department=f"Отдел {i+1}", parent_id=parent_choice.id) 
        db_session.add(dept) 
        db_session.commit()
        choice_department.append(dept)

        boss = Employee(name=person.full_name(), department_id=dept.id, 
                            boss_department=True ) 
        db_session.add(boss) 
        db_session.commit()    
    

    # заполняем сотрудников после подразделений
    
    employees_to_add = []   
    
    for _ in range(count_employees):

        emp = Employee(
            name=person.full_name(),
            department_id=random.choice(choice_department).id,
            boss_department=False
        )
        employees_to_add.append(emp)
        
    db_session.bulk_save_objects(employees_to_add) # потом переделать заполнение департаментов схожим образом списком
    db_session.commit()
    
    elapsed = time.time() - t_start
    print(f"\n Данные заполнены {elapsed:.2f} сек.")
    db_session.close()

def args_process():
    arguments = argparse.ArgumentParser(description="Генерация тестовых данных для приложения")
    arguments.add_argument( '-e', '--employees', type=int, default=5000, help='Сотрудники (по умолчанию: 5000)' ) 
    arguments.add_argument( '-d', '--departments', type=int, default=10, help='Подразделения (по умолчанию: 10)' ) 
    return arguments.parse_args()

def main():
    arguments = args_process()
    try:
        dsn = start_docker() 
    except Exception as e:
        print(f"Не удалось запустить инфраструктуру: {e}")
        return

    
    try:
        generate_data(dsn, count_employees=arguments.employees,count_department=arguments.departments)
    finally:        
        print("Останавливаем контейнер")
        stop_docker()
        print("Работа завершена.")

if __name__ == '__main__':
    main()