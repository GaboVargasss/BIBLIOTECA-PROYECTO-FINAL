import os
from flask import (
    Flask, render_template, redirect, url_for, flash,
    request, jsonify, session
)
from flask_migrate import Migrate
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash

from models.base import db
from models.model import User, Book, Category
from forms import RegistrationForm, ContactForm, BookForm

# Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_key')
app.config['SQLALCHEMY_DATABASE_URI'] = \
    "postgresql+psycopg2://postgres:241210@localhost:5432/biblioteca"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Extensiones
db.init_app(app)
migrate = Migrate(app, db)   # Flask-Migrate
login_manager = LoginManager(app)
login_manager.login_view = 'auth'

# Sincronizar la secuencia de 'users.id' al primer request
from sqlalchemy import text

def sync_user_sequence():
    """Sincroniza la secuencia de users.id con el valor máximo actual."""
    sql = text("SELECT setval('users_id_seq', (SELECT COALESCE(MAX(id),1) FROM users))")
    db.session.execute(sql)
    db.session.commit()

# Carga de usuario para flask-login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Alias para /index.html
app.add_url_rule('/index.html', 'home_html', lambda: redirect(url_for('home')))

# RUTA DE AUTENTICACIÓN
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

# DASHBOARD PRINCIPAL
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

# RUTAS AUXILIARES
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

# API CRUD LIBROS
@app.route('/api/books', methods=['GET', 'POST'])
@login_required
def api_books():
    if request.method == 'GET':
        return jsonify([b.to_dict() for b in Book.query.all()])
    if session.get('role') != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    data = request.get_json()
    book = Book.from_dict(data)
    db.session.add(book)
    db.session.commit()
    return jsonify(book.to_dict()), 201

@app.route('/api/books/<int:id>', methods=['PUT', 'DELETE'])
@login_required
def api_book_detail(id):
    if session.get('role') != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    book = Book.query.get_or_404(id)
    if request.method == 'PUT':
        book.update_from_dict(request.get_json())
        db.session.commit()
        return jsonify(book.to_dict())
    db.session.delete(book)
    db.session.commit()
    return '', 204

if __name__ == '__main__':
    # Sincronizar secuencia antes de iniciar
    with app.app_context():
        sync_user_sequence()
    app.run(debug=True)

