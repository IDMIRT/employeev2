import subprocess
import os
import docker
from pathlib import Path
import time
import sqlite3



def auth_users(current_dir):
    # import sqlite3
    path_db_users = current_dir / 'users.db'
    

    try:

        conn = sqlite3.connect(path_db_users)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM users ORDER BY name") 
        rows = cursor.fetchall() 
        user_list = [(str(row['id']), row['name']) for row in rows] 

        return user_list
    
    except sqlite3.Error as e:         
        return [],f"Ошибка подключения к базе пользователей: {e}" 
    
    finally: 
       if conn is not None: 
           conn.close()

def check_user(user,password,current_dir):
    error = None
    path_db_users = current_dir / 'users.db'
    try:
        conn = sqlite3.connect(path_db_users)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = "SELECT name,password FROM users where name = ?"
        cursor.execute(query, (user,)) 
        row = cursor.fetchone()

        if row:
            user_db = row['name']
            password_db = row['password']
            if user == user_db and password == password_db:
                return True
            else:
                return False, "Пользователь или пароль неверен"
        else:
            error = "Пользователь не найден"
            raise Exception(error)
    except sqlite3.Error as e: 
        print(f"Ошибка БД: {e}") 
    return None


def check_docker():
        
    try:
        subprocess.run(['docker', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # print("Docker установлен")
        return True
    except subprocess.CalledProcessError:
        subprocess.check_call(["winget", "install", "docker-desktop"])
        return True
    except Exception as e:
        # print(f"Произошла ошибка: {e}")
        return False, f"Произошла ошибка: {e}"
    

def start_docker(user,password):
     """
    Запускает контейнер и ВОЗВРАЩАЕТ DSN (строку подключения).
    Не создает таблицы внутри!
    """
     try:
        base_dir = Path(__file__).resolve().parent.parent # Корень проекта
        host_data_path = base_dir / 'data'
        
        if not host_data_path.exists():
            print(f"Папка {host_data_path} не найдена. Создаем её.")
            os.makedirs(host_data_path)

        client = docker.from_env()

        env_vars = {
            "POSTGRES_USER": user,
            "POSTGRES_PASSWORD": password,
            "POSTGRES_DB": "employee"
        }

        # Проверяем, нет ли старого контейнера с таким именем
        try:
            old_container = client.containers.get("iline_employee")
            old_container.remove(force=True)
        except docker.errors.NotFound:
            pass
        
        # container = client.containers.run(
        #     image="postgres:18",
        #     name="iline_employee",
        #     environment=env_vars,
        #     ports={'5432/tcp': 5432},
        #     volumes={
        #         str(host_data_path): {'bind': '/var/lib/postgresql/data', 'mode': 'rw'}
        #     },
        #     detach=True,
        #     tty=True
        # )

        client.containers.run(
            image="postgres:18",
            name="iline_employee",
            environment=env_vars,
            ports={'5432/tcp': 5432},
            volumes={
                str(host_data_path): {'bind': '/var/lib/postgresql/data', 'mode': 'rw'}
            },
            detach=True,
            tty=True)
        
        print("Контейнер запущен. Ожидаем готовность...")
        
        for attempt in range(10):
            try:
                conn_str = f"postgresql+psycopg2://{user}:{password}@localhost:5432/emploee"
                import psycopg2
                conn = psycopg2.connect(conn_str)
                conn.close()
                
                
                return conn_str 
            except Exception:
                time.sleep(2)
                
        raise TimeoutError("PostgreSQL не ответил за отведенное время.")

     except Exception as e:
        print(f"Ошибка запуска Docker: {e}")
        return None

def stop_docker():
    client = docker.from_env()
    container = client.containers.get('iline_employee')
    if container.is_running():
        container.stop()
        # status = container.status

    # if status == 'running':
        # container.stop()
