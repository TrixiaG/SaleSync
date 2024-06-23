#database models
from . import db
from flask_login import UserMixin
from datetime import datetime 
from flask_migrate import Migrate


class User(db.Model, UserMixin):
    eid = db.Column(db.String(8), primary_key=True, unique=True, nullable=False)
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    bday = db.Column(db.String(150), nullable=False)
    access = db.Column(db.String(150), nullable=False)

    def get_id(self):
        return self.eid


class prodInventory(db.Model):
    ptype = db.Column(db.String(50), nullable=False)
    pcode = db.Column(db.String(50), primary_key=True, nullable=False)
    pname = db.Column(db.String(50), unique=True, nullable=False)
    pstock = db.Column(db.Integer, default=0, nullable=False)
    ptimelog = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    puserlog = db.Column(db.String(50), nullable=False)

    def __init__(self, ptype, pcode, pname, pstock, ptimelog, puserlog):
        self.ptype = ptype
        self.pcode = pcode
        self.pname = pname
        self.pstock = pstock
        self.ptimelog = ptimelog
        self.puserlog = puserlog