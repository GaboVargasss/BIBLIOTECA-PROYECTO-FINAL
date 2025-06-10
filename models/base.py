# models/base.py
from flask_sqlalchemy import SQLAlchemy

# Aquí se crea la instancia de SQLAlchemy sin referirse a 'app'
db = SQLAlchemy()
