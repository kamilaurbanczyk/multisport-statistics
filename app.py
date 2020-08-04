from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_pyfile('config.py')
db = SQLAlchemy(app)


class Multisport(db.Model):
    id = db.Column(db.Integer, primary_key= True)
    gender = db.Column(db.String(50))
    category = db.Column(db.String(50), nullable= True)
    classes = db.Column(db.String(50), nullable=False)
    place = db.Column(db.String(50), nullable=False)
    instructor = db.Column(db.String(50), nullable=True)
    duration = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False)


from views import *

if __name__ == "__main__":
    app.run()


