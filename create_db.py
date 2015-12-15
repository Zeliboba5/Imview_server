import os

from app import db
os.remove('app/app.db')
db.create_all()
