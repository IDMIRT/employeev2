from run import db

class Employee(db.Model):
    __tablename__= 'employee'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=False, index=True, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)    


class Department(db.Model):
    __tablename__= 'department'
    id = db.Column(db.Integer, primary_key=True)
    name_department = db.Column(db.String(128), unique=True, index=True, nullable=False)
    boss_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)



