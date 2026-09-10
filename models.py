from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Employee(db.Model):
    __tablename__= 'employee'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=False, index=True, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)  
    boss_department = db.Column(db.Boolean, default=False, nullable=False)  


class Department(db.Model):
    __tablename__= 'department'
    id = db.Column(db.Integer, primary_key=True)
    name_department = db.Column(db.String(128), unique=True, index=True, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)
    



