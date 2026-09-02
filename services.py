import subprocess
import os
import docker
from pathlib import Path
import time
import sqlite3
import tempfile



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

def check_user(user_id,password,current_dir):
    error = None
    path_db_users = current_dir / 'users.db'
    
    try:
        conn = sqlite3.connect(path_db_users)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = "SELECT id,name,password FROM users where id = ?"
        cursor.execute(query, (int(user_id),)) 
        row = cursor.fetchone()

        if row:
            user_id_db = row['id']
            user_db = row['name']
            password_db = row['password']
            if user_id == user_id_db and password == password_db:
                return True,user_db
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
    

def start_docker():
        
    user = "employee" #в дальнейшем подумать, хранить пользователей в env или вытягивать из users.db создав фикированную таблицу
    password = "employee"
    docker_start = False
    temp_env_path = None #область видимости

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.env') as env_file: 
        env_file.write(f"POSTGRES_USER={user}\n") 
        env_file.write(f"POSTGRES_PASSWORD={password}\n") 
        env_file.write("POSTGRES_DB=employees\n") 
        temp_env_path = env_file.name 

    try: # Переходим в папку с docker-compose.yml 
        # os.chdir(current_dir) 
        cmd = [ "docker", "compose", # или "docker-compose" 
               "--env-file", temp_env_path, # Указываем наш временный файл 
               "up", "-d", # -d (detached) как в вашем коде 
               "--build" # На всякий случай пересобрать конфиг 
               ] 
        print("Запуск контейнера через docker compose...") 
        result = subprocess.run(cmd, capture_output=True, text=True, check=True) 
        print(result.stdout) 
        # return True
        docker_start = True
    except subprocess.CalledProcessError as e: 
        print(f"Ошибка Docker:\n{e.stderr}")         
    finally:  
        if os.path.exists(temp_env_path): 
            os.unlink(temp_env_path)

    if docker_start:
        dsn = f"postgresql+psycopg2://{user}:{password}@localhost:5432/employees" #для SQLAlchemy
        import psycopg2
        for starting in range(30): #postgre стартует секунд 10
            try:            
                #для psycopg2 используем прямое подключение               
                conn = psycopg2.connect(f"postgresql://{user}:{password}@localhost:5432/employees")
                conn.close()                
                print("БД готова к работе")
                return dsn 
            except psycopg2.OperationalError as e:
             if "password authentication failed" in str(e) or "database does not exist" in str(e):
                    dsn = None
                    time.sleep(1)        

            except Exception:
                dsn = None
                time.sleep(1)
                
    raise TimeoutError("PostgreSQL не ответил за отведенное время.")


    #  try:
    #     base_dir = Path(__file__).resolve().parent 
    #     database_dir = base_dir / 'data'
        
    #     # if not database_dir.exists(): #лишнее, папка data создается средствами docker
    #     #     print(f"Папка {database_dir} не найдена. Создаем её.")
    #     #     os.makedirs(database_dir)

    #     client = docker.from_env()

    #     env_vars = {
    #         "POSTGRES_USER": user,
    #         "POSTGRES_PASSWORD": password,
    #         "POSTGRES_DB": "employees"
    #     }

    #     # Проверяем, нет ли старого контейнера с таким именем
    #     try:
    #         old_container = client.containers.get("iline_employees")
    #         old_container.remove(force=True)
    #     except docker.errors.NotFound:
    #         pass
        
       
    #     client.containers.run(
    #         image="postgres:18",
    #         name="iline_employees",
    #         environment=env_vars,
    #         ports={'5432/tcp': 5432},
    #         volumes={
    #             str(database_dir): {'bind': '/var/lib/postgresql/data', 'mode': 'rw'}
    #         },
    #         detach=True)
        
    #     print("Контейнер запущен. Ожидаем готовность...")
        
    #     for attempt in range(60): #на range(10) не успевает запустится и проверка падает
    #         import psycopg2
    #         try:
    #             dsn = f"postgresql+psycopg2://{user}:{password}@localhost:5432/employees" #для SQLAlchemy
    #             #для psycopg2 используем прямое подключение               
    #             conn = psycopg2.connect(f"postgresql://{user}:{password}@localhost:5432/employees")
    #             conn.close()                
    #             print("БД готова к работе")
    #             return dsn 
    #         except psycopg2.OperationalError as e:
    #             if "password authentication failed" in str(e) or "database does not exist" in str(e):
    #                 dsn = None
    #                 time.sleep(1)
    #                 continue

    #         except Exception:
    #             dsn = None
    #             time.sleep(1)
                
    #     raise TimeoutError("PostgreSQL не ответил за отведенное время.")

    #  except Exception as e:
    #     print(f"Ошибка запуска Docker: {e}")
    #     return None

def stop_docker():
    try:
        subprocess.run(['docker', 'stop', 'iline_employee'], 
                       check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)        
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при остановке БД: {e.stderr.decode()}")

    # if status == 'running':
        # container.stop()
