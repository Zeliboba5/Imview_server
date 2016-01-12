from app import db
from flask.ext.login import unicode
from datetime import datetime

votes = db.Table('votes',
                 db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                 db.Column('image_id', db.Integer, db.ForeignKey('image.id'))
                 )


class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True)
    path = db.Column(db.String, unique=True)
    publish_date = db.Column(db.DateTime)
    rating = db.Column(db.Integer, default=0)
    comments = db.relationship('Comment', backref='image', lazy='dynamic')
    voted_user = db.relationship('User', secondary=votes,
                                 backref=db.backref('voted_images', lazy='dynamic'))

    def __init__(self, path, rating):
        self.path = path
        self.publish_date = datetime.now()
        self.rating = rating

    def __repr__(self):
        return '<Image %s, %s>' % (self.path, self.rating)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True)
    text = db.Column(db.String)
    publish_date = db.Column(db.DateTime)
    rating = db.Column(db.Integer, default=0)
    image_id = db.Column(db.Integer, db.ForeignKey('image.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, text, user_id, image_id):
        self.text = text
        self.user_id = user_id
        self.image_id = image_id
        self.publish_date = datetime.now()

    def __repr__(self):
        return '<Comment %s, %s, %s Image_id - %s>' % (self.body, self.author, self.text, self.image_id)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String, unique=True)
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    password = db.Column(db.String)

    def get_id(self):
        return unicode(self.id)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def __init__(self, name, password):
        self.name = name
        self.password = password

    def __repr__(self):
        return '<User %s>' % self.name

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
