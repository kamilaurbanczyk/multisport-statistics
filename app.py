from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# set ENV to 'dev' or 'prod'
ENV = 'prod'

app = Flask(__name__)
app.config.from_pyfile('config.py')
db = SQLAlchemy(app)

from config import SQLALCHEMY_DATABASE_URI
engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=False)
Session = sessionmaker(bind=engine)
session = Session()

from views import *

if __name__ == "__main__":
    app.run()
