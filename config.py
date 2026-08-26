import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'my_secret_key'   
    
    # начальная БД для выбора пользователя
    USER_DB_PATH = BASE_DIR / "users.db"
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{USER_DB_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False