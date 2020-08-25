import click
from flask.cli import with_appcontext
from app import db, Multisport, User

@click.command(name='create_tables')
@with_appcontext
def create_tables():
    db.create.all()