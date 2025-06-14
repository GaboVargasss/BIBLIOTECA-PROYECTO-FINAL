import os
from sqlalchemy import case, and_ , or_
from datetime import datetime
from flask import (
    Flask, render_template, redirect, url_for, flash,
    request, jsonify, session, send_from_directory, make_response
)
from models.model import (
    User,               # Modelo original (users)
    Book,               # Modelo original (books)
    Category,           # Modelo original (categories)
    Prestamo,           # Modelo prestamo
    EstadoPrestamo,     # Modelo estado_prestamo
    EstadoEnum,         # Enum para estados
    Usuario,            # Modelo usuario (nuevo)
    Genero,             # Modelo genero
    Autor,              # Modelo autor
    Libro,              # Modelo libro (nuevo)
    Edicion,            # Modelo edicion
    Copia,              # Modelo copia
    AutorLibro,         # Modelo autor_libro
    LibroGenero,        # Modelo libro_genero
    PrestamoEdicion     # Modelo prestamo_edicion
)

# Importaciones adicionales necesarias
from enum import Enum as PyEnum
from sqlalchemy import Enum
from datetime import date
from flask_migrate import Migrate
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func, text
import io
import csv
from models.base import db
from models.model import User, Book, Category, Prestamo
from forms import RegistrationForm, ContactForm, BookForm

# Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_key')
app.config['SQLALCHEMY_DATABASE_URI'] = \
    "postgresql://db_biblioteca_bs8q_user:0m2qLerwHAWHixIsvTztKim01596d1O6@dpg-d16aur8dl3ps7396obb0-a.oregon-postgres.render.com/db_biblioteca_bs8q"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Extensiones
db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'auth'

# Sincronizar secuencias
def sync_sequences():
    """Sincroniza las secuencias de las tablas con los valores máximos actuales"""
    sequences = {
        'users_id_seq': ('users', 'id'),
        'books_id_seq': ('books', 'id'),
        'prestamo_id_prestamo_seq': ('prestamo', 'id_prestamo')
    }
    
    for seq, (table, column) in sequences.items():
        sql = text(f"SELECT setval('{seq}', (SELECT COALESCE(MAX({column}), 1) FROM {table}))")
        db.session.execute(sql)
    db.session.commit()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==============================================
# RUTAS PRINCIPALES (MANTENIDAS)
# ==============================================

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'guest':
            session['role'] = 'guest'
            return redirect(url_for('home'))

        ci  = request.form.get('ci')
        pwd = request.form.get('password')

        if action == 'login':
            user = User.query.filter_by(ci=ci).first()
            if user and check_password_hash(user.password_hash, pwd):
                login_user(user)
                session['role'] = user.role
                return redirect(url_for('home'))
            flash('Cédula o contraseña incorrecta', 'danger')

        elif action == 'register':
            if User.query.filter_by(ci=ci).first():
                flash('Cédula ya registrada', 'warning')
            else:
                user = User(
                    ci=ci,
                    password_hash=generate_password_hash(pwd),
                    role='user'
                )
                db.session.add(user)
                db.session.commit()
                login_user(user)
                session['role'] = 'user'
                return redirect(url_for('home'))

    return render_template('auth.html')

@app.route('/')
def home():
    role = session.get('role')
    if not current_user.is_authenticated and role is None:
        return redirect(url_for('auth'))

    title  = request.args.get('title', '').strip()
    author = request.args.get('author', '').strip()
    cat_id = request.args.get('category', type=int)

    q = Book.query
    if title:
        q = q.filter(Book.title.ilike(f'%{title}%'))
    if author:
        q = q.filter(Book.author.ilike(f'%{author}%'))
    if cat_id:
        q = q.filter_by(category_id=cat_id)
    books = q.all()

    total_books      = len(books)
    total_users      = User.query.count()
    total_categories = Category.query.count()

    cat_data = [
        {'label': c.name, 'count': sum(1 for b in books if b.category_id == c.id)}
        for c in Category.query.all()
    ]
    from collections import Counter
    top_auth = Counter(b.author for b in books).most_common(5)
    top_auth_data = [{'label': a, 'count': n} for a, n in top_auth]

    categories = Category.query.order_by(Category.name).all()

    return render_template(
        'index.html',
        total_books=total_books,
        total_users=total_users,
        total_categories=total_categories,
        cat_data=cat_data,
        top_auth=top_auth_data,
        categories=categories,
        role=role or current_user.role
    )

# ==============================================
# RUTAS AUXILIARES (MANTENIDAS)
# ==============================================

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed = generate_password_hash(form.password.data)
        user = User(
            ci=form.ci.data,
            password_hash=hashed,
            role='user'
        )
        db.session.add(user)
        db.session.commit()
        flash('Registro exitoso. Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('auth'))
    return render_template('registro.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('role', None)
    return redirect(url_for('auth'))

@app.route('/contacto', methods=['GET', 'POST'])
def contacto():
    form = ContactForm()
    if form.validate_on_submit():
        flash('Mensaje enviado con éxito. ¡Gracias!', 'success')
        return redirect(url_for('home'))
    return render_template('contacto.html', form=form)

@app.route('/instalaciones')
def instalaciones():
    return render_template('instalaciones.html')

@app.route('/libros')
def libros():
    form = BookForm()
    cats = Category.query.order_by(Category.name).all()
    form.category.choices = [(c.id, c.name) for c in cats]
    books = Book.query.all()
    return render_template(
        'libros.html',
        form=form,
        books=books,
        role=session.get('role')
    )

@app.route('/masinfo')
def masinfo():
    stats = {
        'total_books': Book.query.count(),
        'total_users': User.query.count(),
        'total_categories': Category.query.count(),
    }
    return render_template('masinfo.html', stats=stats)

# ==============================================
# API PARA LIBROS (MANTENIDAS)
# ==============================================

@app.route('/api/libros/opciones', methods=['GET'])
@login_required
def obtener_opciones_libros():
    try:
        autores = db.session.query(Book.author).distinct().all()
        categorias = Category.query.all()
        
        return jsonify({
            "autores": sorted([a[0] for a in autores if a[0]]),
            "categorias": [{"id": c.id, "name": c.name} for c in categorias]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/libros', methods=['GET'])
@login_required
def obtener_libros():
    """Obtiene todos los libros (con filtros opcionales)"""
    try:
        query = Book.query.options(db.joinedload(Book.category))  # Carga la relación
        
        # Filtros
        if request.args.get('autor'):
            query = query.filter_by(author=request.args.get('autor'))
        if request.args.get('categoria_id'):
            query = query.filter_by(category_id=request.args.get('categoria_id'))
        
        libros = query.all()
        
        return jsonify([{
            "id": libro.id,
            "title": libro.title,
            "author": libro.author,
            "description": libro.description,
            "category": libro.category.name if libro.category else "Sin categoría",  # Cambio clave aquí
            "category_id": libro.category_id
        } for libro in libros])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/libros/<int:id>', methods=['GET'])
@login_required
def obtener_libro(id):
    """Obtiene un libro específico por ID"""
    try:
        libro = Book.query.options(db.joinedload(Book.category)).get_or_404(id)
        return jsonify({
            "id": libro.id,
            "title": libro.title,
            "author": libro.author,
            "description": libro.description,
            "category_id": libro.category_id,
            "category": {
                "id": libro.category.id,
                "name": libro.category.name
            } if libro.category else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 404
@app.route('/api/libros', methods=['POST'])
@login_required
def crear_libro():
    """Crea un nuevo libro"""
    try:
        if session.get('role') != 'admin':
            return jsonify({'error': 'No autorizado'}), 403
            
        if not request.is_json:
            return jsonify({'error': 'El contenido debe ser JSON'}), 400
            
        data = request.get_json()
        
        required_fields = ['title', 'author']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'Campo requerido faltante: {field}'}), 400
        
        nuevo_libro = Book(
            title=data['title'],
            author=data['author'],
            category_id=data.get('category_id'),
            description=data.get('description', '')
        )
        
        db.session.add(nuevo_libro)
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Libro agregado correctamente',
            'libro': {
                "id": nuevo_libro.id,
                "title": nuevo_libro.title,
                "author": nuevo_libro.author,
                "description": nuevo_libro.description,
                "category_id": nuevo_libro.category_id
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/libros/<int:id>', methods=['PUT'])
@login_required
def actualizar_libro(id):
    """Actualiza un libro existente"""
    try:
        libro = Book.query.get_or_404(id)
        
        if session.get('role') != 'admin':
            return jsonify({'error': 'No autorizado'}), 403
            
        if not request.is_json:
            return jsonify({'error': 'El contenido debe ser JSON'}), 400
            
        data = request.get_json()
        
        required_fields = ['title', 'author']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'Campo requerido faltante: {field}'}), 400
        
        libro.title = data['title']
        libro.author = data['author']
        if 'category_id' in data:
            libro.category_id = data['category_id']
        libro.description = data.get('description', libro.description)
        
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Libro actualizado correctamente',
            'libro': {
                "id": libro.id,
                "title": libro.title,
                "author": libro.author,
                "description": libro.description,
                "category_id": libro.category_id
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/libros/<int:id>', methods=['DELETE'])
@login_required
def eliminar_libro(id):
    """Elimina un libro existente"""
    try:
        libro = Book.query.get_or_404(id)
        
        if session.get('role') != 'admin':
            return jsonify({'error': 'No autorizado'}), 403
            
        db.session.delete(libro)
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Libro eliminado correctamente',
            'id': id
        }), 200
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
# ==============================================
# ENDPOINTS PARA USUARIOS (NUEVO)
# ==============================================

@app.route('/api/users', methods=['GET'])
@login_required
def get_users():
    """Obtiene la lista de usuarios para reportes"""
    try:
        if session.get('role') != 'admin':
            return jsonify({'error': 'No autorizado'}), 403

        users = User.query.with_entities(
            User.id,
            User.ci
        ).order_by(User.ci).all()

        return jsonify([{
            'id': user.id,
            'ci': user.ci
        } for user in users])

    except Exception as e:
        app.logger.error(f'Error al obtener usuarios: {str(e)}')
        return jsonify({'error': 'Error al cargar la lista de usuarios'}), 500


# ==============================================
# ENDPOINTS PARA REPORTES (ACTUALIZADOS)
# ==============================================

from datetime import datetime

@app.route('/api/reportes/historial-usuario/<int:user_id>', methods=['GET'])
@login_required
def historial_usuario(user_id):
    """Endpoint seguro que evita completamente el problema del enum"""
    try:
        if session.get('role') != 'admin':
            return jsonify({'error': 'No autorizado'}), 403

        # 1. Consulta directa SQL para evitar el ORM
        sql = text("""
            SELECT 
                p.id_prestamo, 
                p.fecha_prestamo, 
                p.fecha_devolucion, 
                p.precio_alquiler, 
                ep.estado::TEXT as estado_db,  # Convertir a texto directamente
                u.nombre_usuario,
                u.apellido_usuario,
                u.ci,
                u.telefono,
                u.domicilio,
                l.titulo_libro,
                e.isbn
            FROM prestamo p
            JOIN estado_prestamo ep ON p.id_prestamo = ep.id_prestamo
            JOIN usuario u ON p.id_usuario = u.id_usuario
            LEFT JOIN prestamo_edicion pe ON p.id_prestamo = pe.id_prestamo
            LEFT JOIN edicion e ON pe.id_edicion = e.id_edicion
            LEFT JOIN libro l ON e.id_libro = l.id_libro
            WHERE p.id_usuario = :user_id
            ORDER BY p.fecha_prestamo DESC
        """)

        resultados = db.session.execute(sql, {'user_id': user_id}).fetchall()

        # 2. Normalización robusta de estados
        def normalizar_estado(estado_db):
            if not estado_db:
                return 'Desconocido'
            
            estado = str(estado_db).strip().upper()
            return {
                'DEVUELTO': 'Devuelto',
                'PENDIENTE': 'Pendiente',
                'EN_CURSO': 'En curso',
                'EN CURSO': 'En curso',
                'EN_curso': 'En curso',  # Cualquier combinación
                'Devuelto': 'Devuelto',  # Por si acaso
                'Pendiente': 'Pendiente'
            }.get(estado, estado_db)  # Mantener original si no coincide

        # 3. Procesamiento seguro
        if not resultados:
            return jsonify({'error': 'No se encontraron préstamos'}), 404

        # Tomar datos del primer registro (todos son del mismo usuario)
        primer_registro = resultados[0]
        usuario_info = {
            'id': user_id,
            'nombre': primer_registro.nombre_usuario,
            'apellido': primer_registro.apellido_usuario,
            'ci': primer_registro.ci,
            'telefono': primer_registro.telefono,
            'domicilio': primer_registro.domicilio
        }

        prestamos = []
        for row in resultados:
            prestamos.append({
                'id_prestamo': row.id_prestamo,
                'fecha_prestamo': row.fecha_prestamo.strftime('%Y-%m-%d'),
                'fecha_devolucion': row.fecha_devolucion.strftime('%Y-%m-%d') if row.fecha_devolucion else None,
                'precio': float(row.precio_alquiler) if row.precio_alquiler else 0.0,
                'estado': normalizar_estado(row.estado_db),
                'libro': {
                    'titulo': row.titulo_libro,
                    'isbn': row.isbn
                } if row.titulo_libro else None
            })

        return jsonify({
            'usuario': usuario_info,
            'prestamos': prestamos
        })

    except Exception as e:
        app.logger.error(f'Error en historial_usuario (SQL directo): {str(e)}')
        return jsonify({
            'error': 'Error al generar el historial',
            'detalle': str(e)
        }), 500
@app.route('/api/reportes/inventario', methods=['GET'])
@login_required
def inventario():
    """Reporte de inventario de libros"""
    try:
        if session.get('role') != 'admin':
            return jsonify({'error': 'No autorizado'}), 403

        inventario = db.session.query(
            Libro.id_libro,
            Libro.titulo_libro,
            Libro.idioma,
            func.string_agg(Genero.nombre_genero, ', ').label('generos'),
            func.sum(Copia.copias_disponibles).label('copias_disponibles')
        ).join(
            LibroGenero, Libro.id_libro == LibroGenero.id_libro
        ).join(
            Genero, LibroGenero.id_genero == Genero.id_genero
        ).join(
            Edicion, Libro.id_libro == Edicion.id_libro
        ).join(
            Copia, Edicion.id_edicion == Copia.id_edicion
        ).group_by(
            Libro.id_libro
        ).order_by(
            Libro.titulo_libro
        ).all()

        return jsonify([{
            'id': item.id_libro,
            'titulo': item.titulo_libro,
            'idioma': item.idioma,
            'generos': item.generos,
            'copias_disponibles': item.copias_disponibles
        } for item in inventario])

    except Exception as e:
        app.logger.error(f'Error en inventario: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/reportes/prestamos-activos', methods=['GET'])
@login_required
def prestamos_activos():
    """Reporte de préstamos activos corregido"""
    try:
        if session.get('role') != 'admin':
            return jsonify({'error': 'No autorizado'}), 403

        # Consulta corregida con cálculo explícito de días
        prestamos = db.session.query(
            User.ci,
            Libro.titulo_libro,
            Prestamo.fecha_prestamo,
            func.extract('day', func.age(func.current_date(), Prestamo.fecha_prestamo)).label('dias_prestado')
        ).join(
            Prestamo, User.id == Prestamo.id_usuario
        ).join(
            PrestamoEdicion, Prestamo.id_prestamo == PrestamoEdicion.id_prestamo
        ).join(
            Edicion, PrestamoEdicion.id_edicion == Edicion.id_edicion
        ).join(
            Libro, Edicion.id_libro == Libro.id_libro
        ).join(
            EstadoPrestamo, Prestamo.id_prestamo == EstadoPrestamo.id_prestamo
        ).filter(
            EstadoPrestamo.estado == 'En_curso'
        ).order_by(
            Prestamo.fecha_prestamo
        ).all()

        return jsonify([{
            'usuario_ci': p.ci,
            'libro': p.titulo_libro,
            'fecha_prestamo': p.fecha_prestamo.strftime('%Y-%m-%d'),
            'dias_prestado': int(p.dias_prestado)  # Aseguramos que sea entero
        } for p in prestamos])

    except Exception as e:
        app.logger.error(f'Error en prestamos_activos: {str(e)}')
        return jsonify({'error': str(e)}), 500
@app.route('/api/reportes/top-usuarios', methods=['GET'])
@login_required
def top_usuarios():
    """Reporte de usuarios con más préstamos"""
    try:
        if session.get('role') != 'admin':
            return jsonify({'error': 'No autorizado'}), 403

        usuarios = db.session.query(
            User.ci,
            func.count(Prestamo.id_prestamo).label('total_prestamos')
        ).join(
            Prestamo, User.id_usuario == Prestamo.id_usuario
        ).group_by(
            User.ci
        ).order_by(
            func.count(Prestamo.id_prestamo).desc()
        ).limit(10).all()

        return jsonify([{
            'usuario': u.ci,
            'total_prestamos': u.total_prestamos
        } for u in usuarios])

    except Exception as e:
        app.logger.error(f'Error en top_usuarios: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/download/<report_type>', methods=['GET'])
@login_required
def download_report(report_type):
    """Genera y descarga un reporte en CSV"""
    try:
        if session.get('role') != 'admin':
            return jsonify({'error': 'No autorizado'}), 403

        user_id = request.args.get('user_id')
        
        if report_type == 'user_loans' and user_id:
            data = db.session.query(
                Prestamo.id_prestamo,
                Libro.titulo_libro,
                Prestamo.fecha_prestamo,
                Prestamo.fecha_devolucion,
                EstadoPrestamo.estado
            ).join(
                EstadoPrestamo, Prestamo.id_prestamo == EstadoPrestamo.id_prestamo
            ).join(
                PrestamoEdicion, Prestamo.id_prestamo == PrestamoEdicion.id_prestamo
            ).join(
                Edicion, PrestamoEdicion.id_edicion == Edicion.id_edicion
            ).join(
                Libro, Edicion.id_libro == Libro.id_libro
            ).filter(
                Prestamo.id_usuario == user_id
            ).order_by(
                Prestamo.fecha_prestamo.desc()
            ).all()
            print(data)
            title = f"Historial_Prestamos_Usuario_{user_id}"
            headers = ["ID Préstamo", "Libro", "Fecha Préstamo", "Fecha Devolución", "Estado"]
            rows = [
                [p.id_prestamo, p.titulo_libro, 
                 p.fecha_prestamo.strftime('%Y-%m-%d'),
                 p.fecha_devolucion.strftime('%Y-%m-%d'),
                 p.estado]
                for p in data
            ]
        elif report_type == 'inventory':
            data = db.session.query(
                Libro.id_libro,
                Libro.titulo_libro,
                Libro.idioma,
                func.string_agg(Genero.nombre_genero, ', ').label('generos'),
                func.sum(Copia.copias_disponibles).label('copias_disponibles')
            ).join(
                LibroGenero, Libro.id_libro == LibroGenero.id_libro
            ).join(
                Genero, LibroGenero.id_genero == Genero.id_genero
            ).join(
                Edicion, Libro.id_libro == Edicion.id_libro
            ).join(
                Copia, Edicion.id_edicion == Copia.id_edicion
            ).group_by(
                Libro.id_libro
            ).order_by(
                Libro.titulo_libro
            ).all()
            
            title = "Inventario_Libros"
            headers = ["ID", "Título", "Idioma", "Géneros", "Copias Disponibles"]
            rows = [
                [p.id_libro, p.titulo_libro, p.idioma, p.generos, p.copias_disponibles]
                for p in data
            ]   
        elif report_type == 'active_loans':
            data = db.session.query(
                User.id,
                Libro.titulo_libro,
                Prestamo.fecha_prestamo,
                (func.current_date() - Prestamo.fecha_prestamo).label('dias_prestado')
            ).join(
                Prestamo, User.id == Prestamo.id_usuario
            ).join(
                PrestamoEdicion, Prestamo.id_prestamo == PrestamoEdicion.id_prestamo
            ).join(
                Edicion, PrestamoEdicion.id_edicion == Edicion.id_edicion
            ).join(
                Libro, Edicion.id_libro == Libro.id_libro
            ).join(
                EstadoPrestamo, Prestamo.id_prestamo == EstadoPrestamo.id_prestamo
            ).filter(
                EstadoPrestamo.estado == 'En_curso'
            ).order_by(
                Prestamo.fecha_prestamo
            ).all()

            title = "Prestamos_Activos"
            headers = ["ID Usuario", "Libro", "Fecha Préstamo", "Días Prestado"]
            rows = [
                [p.id, p.titulo_libro, 
                p.fecha_prestamo.strftime('%Y-%m-%d'), p.dias_prestado]
                for p in data
            ]

           
        elif report_type == 'top_users':
            data = db.session.query(
                User.ci,
                func.count(Prestamo.id_prestamo).label('total_prestamos')
            ).join(
                Prestamo, User.id == Prestamo.id_usuario
            ).group_by(
                User.ci
            ).order_by(
                func.count(Prestamo.id_prestamo).desc()
            ).limit(10).all()
            
            title = "Top_10_Usuarios"
            headers = ["Usuario", "Total Préstamos"]
            rows = [[u.ci, u.total_prestamos] for u in data]
            
        else:
            return jsonify({'error': 'Tipo de reporte no válido'}), 400

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([title])
        writer.writerow([])
        writer.writerow(headers)
        writer.writerows(rows)
        
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = f'attachment; filename={title}.csv'
        response.headers['Content-type'] = 'text/csv'
        return response
        
    except Exception as e:
        app.logger.error(f'Error en download_report: {str(e)}')
        return jsonify({'error': str(e)}), 500
# ==============================================
# INICIALIZACIÓN
# ==============================================
if __name__ == '__main__':
    with app.app_context():
        sync_sequences()
    app.run(debug=True)
    