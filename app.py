import os
import logging
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET","secret")

# Database configuration: set DATABASE_URL env var to a MySQL URI like
# mysql+pymysql://user:password@host:3306/dbname
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///court.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


class User:
    """Lightweight wrapper for flask-login using the ORM model instance."""
    def __init__(self, user_model):
        self._m = user_model
        self.id = user_model.id
        self.username = user_model.username
        self.email = user_model.email
        self.password_hash = user_model.password_hash
        self.role = user_model.role
        self.full_name = getattr(user_model, 'full_name', '') or ''
        self.phone = getattr(user_model, 'phone', '') or ''
        self.address = getattr(user_model, 'address', '') or ''

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)


@login_manager.user_loader
def load_user(user_id):
    from models import User as UserModel
    user_model = UserModel.query.filter_by(id=user_id).first()
    if user_model:
        return User(user_model)
    return None


from models import *  # ensure models are registered
from routes import *

# Create DB tables if they don't exist (development convenience)
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
 