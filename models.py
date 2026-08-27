from run import db


class User(db.Model):
    __tablename__= 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)


class Employee(db.Model):
    __bind_key__ = 'iline_work'
    __tablename__= 'employee'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=False, index=True, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)    


class Department(db.Model):
    __bind_key__ = 'iline_work'
    __tablename__= 'department'
    id = db.Column(db.Integer, primary_key=True)
    name_department = db.Column(db.String(128), unique=True, index=True, nullable=False)
    boss_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)



