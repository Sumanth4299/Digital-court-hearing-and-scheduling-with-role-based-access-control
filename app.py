import os
import logging
from flask import Flask
from flask_login import LoginManager
from models import db, User, CaseModel, HearingModel, FileModel, MessageModel, AppointmentModel
from dotenv import load_dotenv
logging.basicConfig(level=logging.DEBUG)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "secret")

# MySQL Configuration String linked to user 'sumanth'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql+pymysql://root:fallback@127.0.0.1/court_system')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db.init_app(app)

# File attachment structural processing parameters
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Setup session login management parameters
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
User = User
users_table = User
cases_table = CaseModel
hearings_table = HearingModel
files_table = FileModel
messages_table = MessageModel
appointments_table = AppointmentModel

# Compile and execute the SQL schema inside your workbench instance
with app.app_context():
    db.create_all()

# Import route rules after establishing the table variables
from routes import *

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)