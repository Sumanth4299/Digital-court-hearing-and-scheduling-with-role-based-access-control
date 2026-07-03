from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

# 1. USERS SECURITY IDENTITY TABLE
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'court', 'lawyer', 'client'
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Automated cascading relational hooks
    court_profile = db.relationship('CourtProfile', backref='user', uselist=False, cascade="all, delete-orphan")
    lawyer_profile = db.relationship('LawyerProfile', backref='user', uselist=False, cascade="all, delete-orphan")
    client_profile = db.relationship('ClientProfile', backref='user', uselist=False, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# EXTENDED ENTITY PROFILES
class CourtProfile(db.Model):
    __tablename__ = 'court_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    court_name = db.Column(db.String(100), nullable=False)
    jurisdiction = db.Column(db.String(100), nullable=False)

class LawyerProfile(db.Model):
    __tablename__ = 'lawyer_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    bar_number = db.Column(db.String(50), nullable=False)
    specialization = db.Column(db.String(100), nullable=True)
    law_firm = db.Column(db.String(100), nullable=True)

class ClientProfile(db.Model):
    __tablename__ = 'client_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    case_number = db.Column(db.String(50), nullable=True)
    id_number = db.Column(db.String(50), nullable=False)

# 2. COMPLETE CASES RECORD DATA SCHEMA
class CaseModel(db.Model):
    __tablename__ = 'cases'
    
    id = db.Column(db.Integer, primary_key=True)
    case_number = db.Column(db.String(50), unique=True, nullable=False)
    case_title = db.Column(db.String(200), nullable=False)
    case_type = db.Column(db.String(100), nullable=True)
    plaintiff = db.Column(db.String(100), nullable=True)
    defendant = db.Column(db.String(100), nullable=True)
    lawyer_id = db.Column(db.Integer, nullable=True)
    client_id = db.Column(db.Integer, nullable=True)
    court_id = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(50), default='pending')
    filing_date = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# 3. HEARINGS SCHEDULING DATA SCHEMA
class HearingModel(db.Model):
    __tablename__ = 'hearings'
    
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('cases.id'), nullable=False)
    case_title = db.Column(db.String(200), nullable=True)
    hearing_date = db.Column(db.String(50), nullable=False)  # Stores date string
    hearing_time = db.Column(db.String(50), nullable=True)   # Stores time string
    courtroom = db.Column(db.String(50), nullable=True)
    judge_name = db.Column(db.String(100), nullable=True)
    hearing_type = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='scheduled')

    case = db.relationship('CaseModel', backref=db.backref('hearings_list', lazy=True))

# 4. DIGITAL SECURE STORAGE ARCHIVE DATA SCHEMA
class FileModel(db.Model):
    __tablename__ = 'files'
    id = db.Column(db.String(100), primary_key=True)
    uploader_id = db.Column(db.Integer, nullable=False)
    uploader_name = db.Column(db.String(100), nullable=True)
    uploader_role = db.Column(db.String(50), nullable=True)
    recipient_id = db.Column(db.Integer, nullable=True)
    case_id = db.Column(db.Integer, nullable=True)
    description = db.Column(db.Text, nullable=True)
    encrypted_filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=True)
    file_size = db.Column(db.Integer, nullable=True)
    is_encrypted = db.Column(db.Boolean, default=True)
    encryption_key_a = db.Column(db.Integer, default=5)
    encryption_key_b = db.Column(db.Integer, default=8)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)


# 5. SECURE ENCRYPTED COMMUNICATIONS DATA SCHEMA
class MessageModel(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True) # MySQL auto-increments this automatically!
    sender_id = db.Column(db.Integer, nullable=False)
    sender_name = db.Column(db.String(100), nullable=False)
    sender_role = db.Column(db.String(50), nullable=False)
    recipient_id = db.Column(db.Integer, nullable=True) # Nullable if sent to a whole role
    recipient_role = db.Column(db.String(50), nullable=True)
    subject = db.Column(db.String(200), nullable=True)
    message = db.Column(db.Text, nullable=False)
    is_encrypted = db.Column(db.Boolean, default=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# 7. PUBLIC AD-HOC ENQUIRY TRACKING DATA SCHEMA
class Enquiry(db.Model):
    __tablename__ = 'enquiries'
    id = db.Column(db.Integer, primary_key=True)
    sender_name = db.Column(db.String(100), nullable=False)
    sender_email = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

class AppointmentModel(db.Model):
    __tablename__ = 'appointments'
    
    id = db.Column(db.String(100), primary_key=True) # Supports alphanumeric string keys from generate_id()
    lawyer_id = db.Column(db.Integer, nullable=True)
    lawyer_name = db.Column(db.String(100), nullable=True)
    client_id = db.Column(db.Integer, nullable=True)
    client_name = db.Column(db.String(100), nullable=True)
    case_id = db.Column(db.Integer, nullable=True)
    appointment_date = db.Column(db.String(50), nullable=False)
    appointment_time = db.Column(db.String(50), nullable=True)
    preferred_date = db.Column(db.String(50), nullable=True)     
    preferred_time = db.Column(db.String(50), nullable=True)
    appointment_type = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(200), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='scheduled')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)