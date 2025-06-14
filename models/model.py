from models.base import db
from flask_login import UserMixin
from sqlalchemy import case
from sqlalchemy import Enum
from enum import Enum as PyEnum
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
    password_hash = db.Column(db.Text, nullable=False)
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
class EstadoEnum(PyEnum):
    DEVUELTO = 'Devuelto'
    PENDIENTE = 'Pendiente'
    EN_CURSO = 'En_curso'  # ¡Exactamente como en la BD, con mayúscula y guión bajo!

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuario'
    id_usuario = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(30), nullable=False)
    apellido_usuario = db.Column(db.String(30), nullable=False)
    ci = db.Column(db.String(45), nullable=False, unique=True)
    telefono = db.Column(db.String(20), nullable=False)
    domicilio = db.Column(db.String(350), nullable=False)
    password_hash = db.Column(db.Text)  # Agregado para autenticación
    role = db.Column(db.String(10), default='user')  # Agregado para roles

    def get_id(self):
        return str(self.id_usuario)

class Genero(db.Model):
    __tablename__ = 'genero'
    id_genero = db.Column(db.Integer, primary_key=True)
    nombre_genero = db.Column(db.String(50), nullable=False)
    cantidad_libros = db.Column(db.Integer, nullable=False)

class Autor(db.Model):
    __tablename__ = 'autor'
    id_autor = db.Column(db.Integer, primary_key=True)
    nombre_autor = db.Column(db.String(100), nullable=False)
    nacionalidad = db.Column(db.String(45), nullable=False)
    libros_publicados = db.Column(db.Integer, nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=False)

class Libro(db.Model):
    __tablename__ = 'libro'
    id_libro = db.Column(db.Integer, primary_key=True)
    titulo_libro = db.Column(db.String(50), nullable=False)
    idioma = db.Column(db.String(30), nullable=False)
    numero_paginas = db.Column(db.Integer, nullable=False)
    sinopsis = db.Column(db.String(1000), nullable=False)
    
    # Relaciones
    autores = db.relationship('Autor', secondary='autor_libro', backref='libros')
    generos = db.relationship('Genero', secondary='libro_genero', backref='libros')

class Edicion(db.Model):
    __tablename__ = 'edicion'
    id_edicion = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(45), nullable=False)
    año_publicacion = db.Column(db.Integer, nullable=False)
    id_libro = db.Column(db.Integer, db.ForeignKey('libro.id_libro'), nullable=False)
    
    # Relaciones
    libro = db.relationship('Libro', backref='ediciones')
    copias = db.relationship('Copia', backref='edicion')

class Copia(db.Model):
    __tablename__ = 'copia'
    id_copia = db.Column(db.Integer, primary_key=True)
    copias_disponibles = db.Column(db.Integer, nullable=False)
    id_edicion = db.Column(db.Integer, db.ForeignKey('edicion.id_edicion'), nullable=False)

class Prestamo(db.Model):
    __tablename__ = 'prestamo'
    id_prestamo = db.Column(db.Integer, primary_key=True)
    fecha_prestamo = db.Column(db.Date, nullable=False)
    fecha_devolucion = db.Column(db.Date, nullable=False)
    precio_alquiler = db.Column(db.String(20), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    
    # Relaciones
    usuario = db.relationship('Usuario', backref='prestamos')
    ediciones = db.relationship('Edicion', secondary='prestamo_edicion', backref='prestamos')
    estados = db.relationship('EstadoPrestamo', backref='prestamo')

class EstadoPrestamo(db.Model):
    __tablename__ = 'estado_prestamo'
    id_estado_prestamo = db.Column(db.Integer, primary_key=True)
    estado = db.Column(Enum(EstadoEnum), nullable=False)
    id_prestamo = db.Column(db.Integer, db.ForeignKey('prestamo.id_prestamo'), nullable=False)

# Tablas de asociación
class AutorLibro(db.Model):
    __tablename__ = 'autor_libro'
    id_autor_libro = db.Column(db.Integer, primary_key=True)
    id_autor = db.Column(db.Integer, db.ForeignKey('autor.id_autor'), nullable=False)
    id_libro = db.Column(db.Integer, db.ForeignKey('libro.id_libro'), nullable=False)

class LibroGenero(db.Model):
    __tablename__ = 'libro_genero'
    id_libro_genero = db.Column(db.Integer, primary_key=True)
    id_libro = db.Column(db.Integer, db.ForeignKey('libro.id_libro'), nullable=False)
    id_genero = db.Column(db.Integer, db.ForeignKey('genero.id_genero'), nullable=False)

class PrestamoEdicion(db.Model):
    __tablename__ = 'prestamo_edicion'
    id_prestamo_edicion = db.Column(db.Integer, primary_key=True)
    id_prestamo = db.Column(db.Integer, db.ForeignKey('prestamo.id_prestamo'), nullable=False)
    id_edicion = db.Column(db.Integer, db.ForeignKey('edicion.id_edicion'), nullable=False)