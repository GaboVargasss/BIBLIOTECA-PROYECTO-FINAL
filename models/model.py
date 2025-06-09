# model.py
from sqlalchemy import (
    Column, Integer, String, Date, ForeignKey, Enum, Table
)
from sqlalchemy.orm import relationship
import enum
from base import Base

# ENUM para estado_prestamo
class EstadoEnum(enum.Enum):
    Devuelto = "Devuelto"
    Pendiente = "Pendiente"
    En_curso = "En curso"

# Asociación libro <-> genero
libro_genero = Table(
    "libro_genero", Base.metadata,
    Column("id_libro_genero", Integer, primary_key=True),
    Column("id_libro", Integer, ForeignKey("libro.id_libro")),
    Column("id_genero", Integer, ForeignKey("genero.id_genero"))
)

# Asociación autor <-> libro
autor_libro = Table(
    "autor_libro", Base.metadata,
    Column("id_autor_libro", Integer, primary_key=True),
    Column("id_autor", Integer, ForeignKey("autor.id_autor")),
    Column("id_libro", Integer, ForeignKey("libro.id_libro"))
)

class Usuario(Base):
    __tablename__ = "usuario"
    id_usuario = Column(Integer, primary_key=True, index=True)
    nombre_usuario = Column(String(30), nullable=False)
    apellido_usuario = Column(String(30), nullable=False)
    ci = Column(String(45), nullable=False)
    telefono = Column(String(20), nullable=False)
    domicilio = Column(String(350), nullable=False)

    prestamos = relationship("Prestamo", back_populates="usuario")


class Libro(Base):
    __tablename__ = "libro"
    id_libro = Column(Integer, primary_key=True, index=True)
    titulo_libro = Column(String(50), nullable=False)
    idioma = Column(String(30), nullable=False)
    numero_paginas = Column(Integer, nullable=False)
    sinopsis = Column(String(1000), nullable=False)

    generos = relationship("Genero", secondary=libro_genero, back_populates="libros")
    autores = relationship("Autor", secondary=autor_libro, back_populates="libros")
    ediciones = relationship("Edicion", back_populates="libro")


class Prestamo(Base):
    __tablename__ = "prestamo"
    id_prestamo = Column(Integer, primary_key=True, index=True)
    fecha_prestamo = Column(Date, nullable=False)
    fecha_devolucion = Column(Date, nullable=False)
    precio_alquiler = Column(String(20), nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=False)

    usuario = relationship("Usuario", back_populates="prestamos")
    estado = relationship("EstadoPrestamo", back_populates="prestamo", uselist=False)
    ediciones = relationship("PrestamoEdicion", back_populates="prestamo")


class Genero(Base):
    __tablename__ = "genero"
    id_genero = Column(Integer, primary_key=True, index=True)
    nombre_genero = Column(String(50), nullable=False)
    cantidad_libros = Column(Integer, nullable=False)

    libros = relationship("Libro", secondary=libro_genero, back_populates="generos")


class EstadoPrestamo(Base):
    __tablename__ = "estado_prestamo"
    id_estado_prestamo = Column(Integer, primary_key=True, index=True)
    estado = Column(Enum(EstadoEnum), nullable=False)
    id_prestamo = Column(Integer, ForeignKey("prestamo.id_prestamo"), nullable=False)

    prestamo = relationship("Prestamo", back_populates="estado")


class Autor(Base):
    __tablename__ = "autor"
    id_autor = Column(Integer, primary_key=True, index=True)
    nombre_autor = Column(String(100), nullable=False)
    nacionalidad = Column(String(45), nullable=False)
    libros_publicados = Column(Integer, nullable=False)
    fecha_nacimiento = Column(Date, nullable=False)

    libros = relationship("Libro", secondary=autor_libro, back_populates="autores")


class Edicion(Base):
    __tablename__ = "edicion"
    id_edicion = Column(Integer, primary_key=True, index=True)
    isbn = Column(String(45), nullable=False)
    año_publicacion = Column("año_publicacion", Integer, nullable=False)
    id_libro = Column(Integer, ForeignKey("libro.id_libro"), nullable=False)

    libro = relationship("Libro", back_populates="ediciones")
    copias = relationship("Copia", back_populates="edicion")
    prestamos = relationship("PrestamoEdicion", back_populates="edicion")


class PrestamoEdicion(Base):
    __tablename__ = "prestamo_edicion"
    id_prestamo_edicion = Column(Integer, primary_key=True, index=True)
    id_prestamo = Column(Integer, ForeignKey("prestamo.id_prestamo"), nullable=False)
    id_edicion = Column(Integer, ForeignKey("edicion.id_edicion"), nullable=False)

    prestamo = relationship("Prestamo", back_populates="ediciones")
    edicion = relationship("Edicion", back_populates="prestamos")


class Copia(Base):
    __tablename__ = "copia"
    id_copia = Column(Integer, primary_key=True, index=True)
    copias_disponibles = Column(Integer, nullable=False)
    id_edicion = Column(Integer, ForeignKey("edicion.id_edicion"), nullable=False)

    edicion = relationship("Edicion", back_populates="copias")
