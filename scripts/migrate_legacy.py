# scripts/migrate_legacy.py

import os, sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 1) Asegura que el root del proyecto esté en sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import app
from models.base import db
from models.model import User, Category, Book

LEGACY_DB_URL = "postgresql+psycopg2://postgres:241210@localhost:5432/biblioteca"
legacy_engine = create_engine(LEGACY_DB_URL)
LegacySession = sessionmaker(bind=legacy_engine)
legacy_sess = LegacySession()

with app.app_context():
    session = db.session
    session.expire_on_commit = False

    # 1) Migrar usuarios
    print("Migrando usuarios...")
    for row in legacy_sess.execute(text(
        "SELECT id_usuario AS id, ci FROM usuario"
    )):
        if not session.query(User).filter_by(ci=row.ci).first():
            session.add(User(
                id=row.id,
                ci=row.ci,
                password_hash='',
                role='user'
            ))
    session.commit()

    # 2) Migrar categorías
    print("Migrando categorías...")
    for row in legacy_sess.execute(text(
        "SELECT id_genero AS id, nombre_genero AS name FROM genero"
    )):
        # Evita duplicados por nombre
        if not session.query(Category).filter_by(name=row.name).first():
            session.add(Category(id=row.id, name=row.name))
    session.commit()

    # 3) Preparar mappings para libros
    print("Preparando mappings de autor y categoría para libros...")
    cat_map = {
        lg.id_libro: lg.id_genero
        for lg in legacy_sess.execute(text(
            "SELECT id_libro, id_genero FROM libro_genero"
        ))
    }
    auth_map = {}
    for row in legacy_sess.execute(text("""
        SELECT al.id_libro, a.nombre_autor
        FROM autor_libro al
        JOIN autor a ON al.id_autor = a.id_autor
    """)):
        auth_map.setdefault(row.id_libro, row.nombre_autor)

    # 4) Migrar libros
    print("Migrando libros...")
    for row in legacy_sess.execute(text(
        "SELECT id_libro AS id, titulo_libro AS title, sinopsis AS description FROM libro"
    )):
        if not session.query(Book).get(row.id):
            session.add(Book(
                id=row.id,
                title=row.title,
                author=auth_map.get(row.id, 'Desconocido'),
                description=row.description,
                category_id=cat_map.get(row.id)
            ))
    session.commit()

print("✅ Migración legacy completada.")
legacy_sess.close()
