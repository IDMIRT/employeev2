from pathlib import Path

current_dir = Path(__file__).resolve().parent


def auth_users():
    import sqlite3
    path_db_users = current_dir / 'users.db'
    try:
        conn = sqlite3.connect(path_db_users)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM users ORDER BY name") 
        rows = cursor.fetchall() 
        user_list = [(str(row['id']), row['name']) for row in rows] 
        return user_list
    except:

