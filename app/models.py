from app import db


class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True)
    path = db.Column(db.String, unique=True)
    title = db.Column(db.String, default="Без названия")
    description = db.Column(db.String, default="Без описания")
    rating = db.Column(db.Integer, default=0)
    is_featured = db.Column(db.Boolean, default=False)
    comments = db.relationship('Comment', backref='image', lazy='dynamic')

    def __init__(self, path, title, description, rating, is_featured):
        self.path = path
        self.title = title
        self.description = description
        self.rating = rating
        self.is_featured = is_featured

    def __repr__(self):
        return '<Image %s, %s, %s, %s>' % (self.path, self.title, self.description, self.rating)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True)
    text = db.Column(db.String)
    image_id = db.Column(db.Integer, db.ForeignKey('image.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Comment %s, %s, %s Image_id - %s>' % (self.body, self.author, self.text, self.image_id)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String, default='anonymous')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')

    def __repr__(self):
        return '<User %s>' % self.name

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
