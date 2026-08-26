from run import db
from sqlalchemy import Column,String,Integer


class User(db.Model):
    __tablename__= 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True, index=True, nullable=False)
    password = Column(String(128), nullable=False)