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
    

def start_container_db(client):
    stop_check = time.time() + 180
    try:
        docker_container = client.containers.get('iline_employee')
    except Exception:
        raise RuntimeError("Контейнер 'iline_employee' не найден. Убедитесь, что он успешно запустился через docker-compose.") 
    
    print('Ожидаем запуск контейнера')
            
    while time.time() < stop_check:
        try:
            docker_container.reload()
            health_status = docker_container.attrs['State'].get('Health', {}).get('Status')

            if health_status == 'healthy': 
                print("БД здорова согласно healthcheck, можно подключаться")                 
                return True
            
            if docker_container.status in ('exited', 'dead', 'removing'): 
                logs = docker_container.logs(tail=20).decode('utf-8') 
                raise RuntimeError( f"Контейнер перешел в статус '{docker_container.status}'. Ожидание прервано.\nПоследние логи:\n{logs}" )
            
            if int(time.time()) % 10 == 0: 
                print(f"Текущий статус: {health_status or 'starting'}... Осталось ~{int(stop_check - time.time())} сек.") 

        except docker.errors.APIError as e: 
            print(f"Временная ошибка при обращении к Docker API: {e}. Повтор...")
            time.sleep(3) 
                
    docker_container.reload() 
    final_status = docker_container.attrs['State'].get('Health', {}).get('Status') 
    current_logs = docker_container.logs(tail=50).decode('utf-8') 
                
    raise TimeoutError( f"Контейнер iline_employee не запустился за отведенное время (180 сек).\n")

def check_start_db(user,password):
    # dsn = f"postgresql+psycopg2://{user}:{password}@localhost:5432/employees" #для SQLAlchemy
    dsn = None
    import psycopg2
    for starting in range(180): #postgre стартует секунд 10
        print(f"Поытка подключения к БД №{starting}")
        try:            
            #для psycopg2 используем прямое подключение                           
            conn = psycopg2.connect(f"postgresql://{user}:{password}@localhost:5432/employees")
            conn.close()    
            dsn = f"postgresql+psycopg2://{user}:{password}@localhost:5432/employees" #для SQLAlchemy            
            print("БД готова к работе")            
            return dsn 
            
        except psycopg2.OperationalError as e:

            err_str = str(e)

            if "password authentication failed" in err_str or "no pg_hba.conf entry" in err_str: 
                raise RuntimeError(f"Ошибка авторизации: {err_str}")

            if "does not exist" in err_str and "accepting connections" in err_str: 
                print("Сервер запущен, но таблицы инициализируются...") 
                time.sleep(5) 
                continue

            time.sleep(1)

        except psycopg2.InterfaceError as e: 
            time.sleep(1)                    

        except Exception:            
            time.sleep(5)

    if not dsn:
        raise TimeoutError("PostgreSQL не ответил за отведенное время.")

    return dsn
    

def start_docker():
        
    user = "employee" #в дальнейшем подумать, хранить пользователей в env или вытягивать из users.db создав фикированную таблицу
    password = "employee"
    db_dir = Path(__file__).resolve().parent/'data' #для хранения данных
    docker_start = False    
    temp_env_path = None #область видимости    
    postgre_dir = '/var/lib/postgresql'     
    client = docker.from_env()
    # в windows папка data создается с правами пользователя системы, поэтому
    # используем другой контейнер для создания папки /data с правами all решение так себе, но другого способа не нашел
    if not db_dir.exists(): 
        
        print("Не найдена папка для БД, создаем для работы приложения") 
        client.containers.run(image="alpine", # Легковесный образ 
                                     command=f"sh -c 'mkdir -p {postgre_dir} && chown -R 999:999 {postgre_dir}'", 
                                     volumes={db_dir: {'bind': postgre_dir, 'mode': 'rw'}}, 
                                     detach=False, # Выполнить и выйти 
                                     remove=True # Удалить за собой сразу после выполнения 
                                     )

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.env') as env_file: 
        env_file.write(f"POSTGRES_USER={user}\n") 
        env_file.write(f"POSTGRES_PASSWORD={password}\n")         
        temp_env_path = env_file.name 

    try:          
        cmd = [ "docker", "compose", 
               "--env-file", temp_env_path, 
               "up", "-d" 
               ] 
        print("Запуск контейнера через docker compose...") 
        result = subprocess.run(cmd, capture_output=True, text=True, check=True) 
        print(result.stdout)         
        docker_start = True

    except subprocess.CalledProcessError as e: 
        print(f"Ошибка Docker:\n{e.stderr}")         

    finally:  
        if os.path.exists(temp_env_path): 
            os.unlink(temp_env_path)


    dsn = check_start_db(user,password)
    return dsn


# start_docker()


def stop_docker():
    try:
        subprocess.run(['docker', 'stop', 'iline_employee'], 
                       check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)        
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при остановке БД: {e.stderr.decode()}")

    # if status == 'running':
        # container.stop()

# stop_docker()