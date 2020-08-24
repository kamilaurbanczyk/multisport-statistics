from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# set ENV to 'dev' or 'prod'
ENV = 'dev'

app = Flask(__name__)
app.config.from_pyfile('config.py')
db = SQLAlchemy(app)


class Multisport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gender = db.Column(db.String(50))
    category = db.Column(db.String(50), nullable=True)
    classes = db.Column(db.String(50), nullable=False)
    place = db.Column(db.String(50), nullable=False)
    instructor = db.Column(db.String(50), nullable=True)
    duration = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    classes_rate = db.Column(db.Integer, nullable=True)
    training_rate = db.Column(db.Integer, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gender = db.Column(db.String(50))
    username = db.Column(db.String(70), unique=True)
    email = db.Column(db.String(200))
    password = db.Column(db.String(100))
    join_date = db.Column(db.DateTime)

    activities = db.relationship('Multisport', backref='user', lazy='dynamic')


from views import *

if __name__ == "__main__":
    app.run()
