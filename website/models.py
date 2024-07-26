from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tmdb_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(150), nullable=False)
    cover_url = db.Column(db.String(300), nullable=False)
    watched = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    movies = db.relationship('Movie')
