from models.base import db
from flask_login import UserMixin

class Category(db.Model):
    __tablename__ = 'categories'
    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    books= db.relationship('Book', backref='category', lazy=True)

    def to_dict(self):
        return {'id':self.id,'name':self.name}

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    ci            = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role          = db.Column(db.String(10), nullable=False, default='user')

    def to_dict(self):
        return {'id':self.id,'ci':self.ci,'role':self.role}

class Book(db.Model):
    __tablename__ = 'books'
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(128), nullable=False)
    author      = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))

    def to_dict(self):
        return {
            'id':self.id,'title':self.title,'author':self.author,
            'description':self.description,
            'category': self.category.name if self.category else None,
            'category_id':self.category_id
        }

    @classmethod
    def from_dict(cls,data):
        return cls(
            title=data.get('title'),
            author=data.get('author'),
            description=data.get('description'),
            category_id=data.get('category_id')
        )

    def update_from_dict(self,data):
        for f in ['title','author','description','category_id']:
            if f in data: setattr(self,f,data[f])
