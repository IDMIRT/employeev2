from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select, case
from sqlalchemy.orm import column_property,aliased

db = SQLAlchemy()

class Department(db.Model):
    __tablename__= 'department'
    id = db.Column(db.Integer, primary_key=True)
    name_department = db.Column(db.String(128), unique=True, index=True, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)

    employee = db.relationship('Employee', back_populates="department")

    # @property 
    # def boss(self):         
    #     for emp in self.employees: 
    #         if emp.boss_department: 
    #             return emp 
    #     return None


class Employee(db.Model):
    __tablename__= 'employee'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=False, index=True, nullable=False)
    employee_position=db.Column(db.Text,nullable=False)
    salary = db.Column(db.Numeric(10,2))
    date_employment= db.Column(db.Date, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)  
    boss_department = db.Column(db.Boolean, default=False, nullable=False)  
    
    department  = db.relationship("Department", back_populates="employee")

    # boss_name = column_property(select(Employee.name).where((Employee.department_id == department_id)&(Employee.boss_department == True)).limit(1).scalar_subquery() )
    boss_name = column_property( 
        # Используем СТРОКОВОЕ имя класса "employee" вместо Employee.name 
        select(case((
             # Условие: в том же отделе есть босс с другим именем 
             (department_id == aliased(__tablename__, name='boss').department_id)&
             (aliased(__tablename__, name='boss').boss_department == True)&
             (aliased(__tablename__, name='boss').name != name)), 
             aliased(__tablename__, name='boss').name, else_='—' ).label('boss_name')).correlate_except(__tablename__).scalar_subquery() )

    



