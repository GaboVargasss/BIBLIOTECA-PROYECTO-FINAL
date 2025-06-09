# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy.exc import NoResultFound
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models.base import Base, engine, SessionLocal
from models.model import Usuario, Libro, Genero, Autor, Prestamo, EstadoPrestamo, Edicion, Copia, PrestamoEdicion, EstadoEnum
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret")

# Crear tablas si no existen
Base.metadata.create_all(bind=engine)

# Sesión DB y Login
db = SessionLocal()
login_manager = LoginManager(app)
login_manager.login_view = "auth"

@login_manager.user_loader
def load_user(user_id):
    return db.query(Usuario).get(int(user_id))

@app.context_processor
def inject_user():
    return dict(username=(current_user.nombre_usuario if current_user.is_authenticated else ""))

# --- Rutas de auth ---
@app.route("/", methods=["GET","POST"])
def auth():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method=="POST":
        action = request.form.get("action")
        nombre = request.form["nombre_usuario"].strip()
        apellido = request.form["apellido_usuario"].strip()
        ci = request.form["ci"].strip()
        tel = request.form["telefono"].strip()
        dom = request.form["domicilio"].strip()
        if action=="register":
            u = Usuario(nombre_usuario=nombre, apellido_usuario=apellido,
                        ci=ci, telefono=tel, domicilio=dom)
            db.add(u); db.commit()
            flash("Usuario creado, ahora inicia sesión","success")
            return redirect(url_for("auth"))
        elif action=="login":
            # en este esquema no hay password, así que login directo por ci
            try:
                u = db.query(Usuario).filter_by(ci=ci).one()
                login_user(u)
                return redirect(url_for("dashboard"))
            except NoResultFound:
                flash("CI no registrado","danger")
    return render_template("auth.html")

@app.route("/logout")
@login_required
def logout():
    logout_user(); flash("Cerraste sesión","info")
    return redirect(url_for("auth"))

# --- Dashboard principal ---
@app.route("/dashboard")
@login_required
def dashboard():
    # estadísticas básicas
    stats = {
        "total_usuarios": db.query(Usuario).count(),
        "total_libros": db.query(Libro).count(),
        "total_copias": db.query(Copia).count(),
        "prestamos_pendientes": db.query(EstadoPrestamo).filter_by(estado=EstadoEnum.Pendiente).count()
    }
    return render_template("dashboard.html", stats=stats)

# --- APIs de ejemplo ---
@app.route("/api/libros")
@login_required
def api_libros():
    lst = db.query(Libro).all()
    return jsonify([{
        "id": l.id_libro,
        "titulo": l.titulo_libro,
        "idioma": l.idioma,
        "paginas": l.numero_paginas,
        "sinopsis": l.sinopsis
    } for l in lst])

@app.route("/api/usuarios")
@login_required
def api_usuarios():
    lst = db.query(Usuario).all()
    return jsonify([{
        "id": u.id_usuario,
        "nombre": u.nombre_usuario,
        "apellido": u.apellido_usuario,
        "ci": u.ci
    } for u in lst])

# errores
@app.errorhandler(404)
def not_found(e): return render_template("404.html"), 404
@app.errorhandler(500)
def server_error(e): return render_template("500.html"), 500

if __name__ == "__main__":
    app.run(debug=True)
