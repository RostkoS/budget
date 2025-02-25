
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    family_id = db.Column(db.Integer, db.ForeignKey('family.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)

    family = relationship('Family', backref='categories')

    __table_args__ = (
        UniqueConstraint('family_id', 'name', name='uix_family_name'),
    )


record_tags = db.Table(
    'record_tags',
    db.Column('record_id', db.Integer, db.ForeignKey('record.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    family_id = db.Column(db.Integer, db.ForeignKey('family.id'))  
    family = db.relationship('Family', back_populates='members', foreign_keys=[family_id]) 
    
    records = db.relationship('Record', backref='user', lazy='dynamic')

    @property
    def total_income(self):
        return sum(record.amount for record in self.records.filter_by(type='дохід'))

    @property
    def total_expenses(self):
        return sum(record.amount for record in self.records.filter_by(type='витрата'))

    @property
    def net_balance(self):
        return self.total_income - self.total_expenses


class Family(db.Model):
    __tablename__ = 'family' 
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))  
    owner = db.relationship('User', backref='owner_of_family', foreign_keys=[owner_id])  
    
    members = db.relationship('User', back_populates='family', foreign_keys=[User.family_id]) 


class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    family_id = db.Column(db.Integer, db.ForeignKey('family.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id')) 
    date = db.Column(db.String(10), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    tags = db.relationship('Tag', secondary=record_tags, backref=db.backref('records', lazy='dynamic'))


class Invite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    family_id = db.Column(db.Integer, db.ForeignKey('family.id'))
    email = db.Column(db.String(100), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    used = db.Column(db.Boolean, default=False)
