import os
import time
from pathlib import Path
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker


from services import auth_users, check_user, start_docker, stop_docker, docker 
from models import db, Employee, Department
from mimesis import Person, Generic
from mimesis.locales import Locale
import random

def generate_data(dsn=None, count_employees=5000):
    """
    Функция очистки и заполнения рабочей БД PostgreSQL.
    Работает автономно от Flask.
    """
    print(f"Подключение к целевой БД: {dsn}")

    # if not dsn: #потом сделать загрузку из env
    #     dsn = 'postgresql+psycopg2://employee:employee@localhost:5432/employees'
    
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
    generic = Generic(Locale.RU)
    names_department = ["Приемки", "Контроля", "Сбыта", "Бухгалтерия", "Безопасность", "Документооборота"]

    departments_by_level = {1: [], 2: [], 3: [], 4: [], 5: []}
    
    t_start = time.time()
    
    # --- Создание дерева ---
    root_dept = Department(name_department="ООО 'Рога и копыта'")
    db_session.add(root_dept)
    db_session.commit() # Нужен ID корня
    current_parents = [root_dept]

    for level in range(1, 6): 
        depts_choice = names_department
        num_depts = random.randint(3, 8) 
        new_level_depts = [] 
        for i in range(num_depts): 
            parent_choice = random.choice(depts_choice) 
            depts_choice.remove(parent_choice)
            dept_name = parent_choice
            dept = Department(name_department=dept_name, parent_id=parent_choice.id) 
            db_session.add(dept) # Добавляем в сессию, чтобы сгенерировался ID # Сразу создаем начальника ДЛЯ ЭТОГО ОТДЕЛА 
            boss = Employee(name=person.full_name(), department_id=None, # Пока None, обновим после commit 
                            boss_department=True ) 
            db_session.add(boss) # Сохраняем кортеж (отдел, объект_босса), чтобы связать их позже 
            new_level_depts.append({'department': dept, 'boss': boss}) 
            # Фиксируем изменения в БД, чтобы появились ID 
            db_session.commit() # Теперь, когда у отделов есть ID, привязываем к ним боссов 

        for item in new_level_depts: 
            item['boss'].department_id = item['department'].id 

        db_session.commit() # Сохраняем связь Boss -> Department
        for d in new_level_depts: 
            db_session.refresh(d)

    

    # --- Сотрудники ---
    leaf_departments = departments_by_level[5]
    employees_to_add = []   
    
    for people in range(count_employees):

        emp = Employee(
            name=person.full_name(),
            department_id=random.choice(leaf_departments).id,
            boss_department=False
        )
        employees_to_add.append(emp)
        
    db_session.bulk_save_objects(employees_to_add)
    db_session.commit()
    
    elapsed = time.time() - t_start
    print(f"\n✅ Данные успешно записаны за {elapsed:.2f} сек.")
    db_session.close()

def main():
    """Главная точка входа"""
    
    
    
    try:
        dsn = start_docker() 
    except Exception as e:
        print(f"Не удалось запустить инфраструктуру: {e}")
        return

    # 3. Генерация данных
    try:
        generate_data(dsn, count_employees=5000)
    finally:
        # 4. Остановка контейнера (опционально, можно закомментировать для dev-среды)
        print("\nОстанавливаем тестовый контейнер...")
        stop_docker()
        print("Работа завершена.")

if __name__ == '__main__':
    main()