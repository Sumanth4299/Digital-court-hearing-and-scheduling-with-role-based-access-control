import os
import uuid
import base64
from datetime import datetime
from flask import render_template, redirect, url_for, request, flash, send_file, abort, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import or_
from app import app, db, User as LoginUser
from models import User as UserModel, Case as CaseModel, Hearing as HearingModel, File as FileModel, Message as MessageModel, Appointment as AppointmentModel
from affine import affine_encrypt, affine_decrypt

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_id():
    return str(uuid.uuid4())[:8]


@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'court':
            return redirect(url_for('court_dashboard'))
        elif current_user.role == 'lawyer':
            return redirect(url_for('lawyer_dashboard'))
        elif current_user.role == 'client':
            return redirect(url_for('client_dashboard'))
    return render_template('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    role = None

    if request.method == 'POST':
        role = request.form.get('role')
        username = request.form.get('username')

        # CONDITION A: User just picked a role, but hasn't filled out details yet
        if role and not username:
            return render_template('signup.html', role=role)

        # CONDITION B: User is submitting the full registration data
        elif role and username:
            email = request.form.get('email')
            password = request.form.get('password')
            full_name = request.form.get('full_name')
            phone = request.form.get('phone')
            address = request.form.get('address')
            
            # Database unique validation checks
            if UserModel.query.filter_by(username=username).first():
                flash('Username already exists', 'error')
                return render_template('signup.html', role=role)
            if UserModel.query.filter_by(email=email).first():
                flash('Email already registered', 'error')
                return render_template('signup.html', role=role)
            
            # Construct user payload
            user_model = UserModel(
                id=generate_id(),
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                role=role,
                full_name=full_name,
                phone=phone,
                address=address,
                created_at=datetime.now()
            )
            
            # Handle role-based custom data fields
            if role == 'court':
                user_model.court_name = request.form.get('court_name', '')
                user_model.jurisdiction = request.form.get('jurisdiction', '')
            elif role == 'lawyer':
                user_model.bar_number = request.form.get('bar_number', '')
                user_model.specialization = request.form.get('specialization', '')
                user_model.law_firm = request.form.get('law_firm', '')
            elif role == 'client':
                user_model.case_number = request.form.get('case_number', '')
                user_model.id_number = request.form.get('id_number', '')

            db.session.add(user_model)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
    # FIXED LINE: This is now aligned perfectly with 4 spaces (same level as 'if request.method == ...')
    return render_template('signup.html', role=role)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user_model = UserModel.query.filter_by(username=username).first()

        if user_model and check_password_hash(user_model.password_hash, password):
            user = LoginUser(user_model)
            login_user(user)
            flash('Login successful!', 'success')
            
            if user.role == 'court':
                return redirect(url_for('court_dashboard'))
            elif user.role == 'lawyer':
                return redirect(url_for('lawyer_dashboard'))
            elif user.role == 'client':
                return redirect(url_for('client_dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@app.route('/court/dashboard')
@login_required
def court_dashboard():
    if current_user.role != 'court':
        abort(403)
    lawyers = UserModel.query.filter_by(role='lawyer').all()
    clients = UserModel.query.filter_by(role='client').all()
    all_cases = CaseModel.query.all()
    all_hearings = HearingModel.query.all()
    
    return render_template('court/dashboard.html', 
                         lawyers=lawyers, 
                         clients=clients,
                         cases=all_cases,
                         hearings=all_hearings)


@app.route('/court/schedule-hearings', methods=['GET', 'POST'])
@login_required
def court_schedule_hearings():
    if current_user.role != 'court':
        abort(403)
    
    if request.method == 'POST':
        hearing = HearingModel(
            id=generate_id(),
            case_id=request.form.get('case_id'),
            case_title=request.form.get('case_title'),
            hearing_date=request.form.get('hearing_date'),
            hearing_time=request.form.get('hearing_time'),
            courtroom=request.form.get('courtroom'),
            judge_name=request.form.get('judge_name'),
            hearing_type=request.form.get('hearing_type'),
            notes=request.form.get('notes'),
            created_by=current_user.id,
            created_at=datetime.now(),
            status='scheduled'
        )
        db.session.add(hearing)
        db.session.commit()
        flash('Hearing scheduled successfully!', 'success')
        return redirect(url_for('court_schedule_hearings'))
    
    all_cases = CaseModel.query.all()
    all_hearings = HearingModel.query.all()
    return render_template('court/schedule_hearings.html', cases=all_cases, hearings=all_hearings)


@app.route('/court/manage-cases', methods=['GET', 'POST'])
@login_required
def court_manage_cases():
    if current_user.role != 'court':
        abort(403)
    
    if request.method == 'POST':
        case = CaseModel(
            id=generate_id(),
            case_number=request.form.get('case_number'),
            case_title=request.form.get('case_title'),
            case_type=request.form.get('case_type'),
            plaintiff=request.form.get('plaintiff'),
            defendant=request.form.get('defendant'),
            lawyer_id=request.form.get('lawyer_id'),
            client_id=request.form.get('client_id'),
            status=request.form.get('status', 'pending'),
            filing_date=request.form.get('filing_date'),
            description=request.form.get('description'),
            created_by=current_user.id,
            created_at=datetime.now()
        )
        db.session.add(case)
        db.session.commit()
        flash('Case created successfully!', 'success')
        return redirect(url_for('court_manage_cases'))
    
    lawyers = UserModel.query.filter_by(role='lawyer').all()
    clients = UserModel.query.filter_by(role='client').all()
    all_cases = CaseModel.query.all()
    return render_template('court/manage_cases.html', cases=all_cases, lawyers=lawyers, clients=clients)


@app.route('/court/view-users')
@login_required
def court_view_users():
    if current_user.role != 'court':
        abort(403)
    lawyers = UserModel.query.filter_by(role='lawyer').all()
    clients = UserModel.query.filter_by(role='client').all()
    return render_template('court/view_users.html', lawyers=lawyers, clients=clients)


@app.route('/court/share-info', methods=['GET', 'POST'])
@login_required
def court_share_info():
    if current_user.role != 'court':
        abort(403)
    
    if request.method == 'POST':
        message = MessageModel(
            id=generate_id(),
            sender_id=current_user.id,
            sender_name=current_user.full_name or current_user.username,
            sender_role=current_user.role,
            recipient_id=request.form.get('recipient_id'),
            recipient_role=request.form.get('recipient_role'),
            subject=request.form.get('subject'),
            message=request.form.get('message'),
            is_encrypted=(request.form.get('encrypt') == 'on'),
            created_at=datetime.now(),
            read=False
        )
        if message.is_encrypted and message.message:
            message_bytes = message.message.encode('utf-8')
            encrypted = affine_encrypt(message_bytes)
            message.message = base64.b64encode(encrypted).decode('utf-8')

        db.session.add(message)
        db.session.commit()
        flash('Message sent successfully!', 'success')
        return redirect(url_for('court_share_info'))
    
    lawyers = UserModel.query.filter_by(role='lawyer').all()
    clients = UserModel.query.filter_by(role='client').all()

    sent_messages = MessageModel.query.filter_by(sender_id=current_user.id).all()
    received_messages = MessageModel.query.filter(
        or_(MessageModel.recipient_id == current_user.id, MessageModel.recipient_role == 'court')
    ).all()
    
    return render_template('court/share_info.html', 
                         lawyers=lawyers, 
                         clients=clients,
                         sent_messages=sent_messages,
                         received_messages=received_messages)


@app.route('/court/view-schedules')
@login_required
def court_view_schedules():
    if current_user.role != 'court':
        abort(403)
    
    all_hearings = HearingModel.query.all()
    all_appointments = AppointmentModel.query.all()
    return render_template('court/view_schedules.html', hearings=all_hearings, appointments=all_appointments)


@app.route('/lawyer/dashboard')
@login_required
def lawyer_dashboard():
    if current_user.role != 'lawyer':
        abort(403)
    
    my_cases = CaseModel.query.filter_by(lawyer_id=current_user.id).all()

    my_files = FileModel.query.filter(
        or_(FileModel.uploader_id == current_user.id, FileModel.recipient_id == current_user.id)
    ).all()

    all_hearings = HearingModel.query.all()

    return render_template('lawyer/dashboard.html', 
                         cases=my_cases,
                         files=my_files,
                         hearings=all_hearings)


@app.route('/lawyer/view-cases')
@login_required
def lawyer_view_cases():
    if current_user.role != 'lawyer':
        abort(403)
    my_cases = CaseModel.query.filter_by(lawyer_id=current_user.id).all()
    all_cases = CaseModel.query.all()
    return render_template('lawyer/view_cases.html', my_cases=my_cases, all_cases=all_cases)


@app.route('/lawyer/upload-files', methods=['GET', 'POST'])
@login_required
def lawyer_upload_files():
    if current_user.role != 'lawyer':
        abort(403)
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('lawyer_upload_files'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('lawyer_upload_files'))
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_id = generate_id()
            
            file_content = file.read()
            encrypted_content = affine_encrypt(file_content)
            
            encrypted_filename = f"enc_{file_id}_{filename}"
            encrypted_path = os.path.join(app.config['UPLOAD_FOLDER'], encrypted_filename)
            
            with open(encrypted_path, 'wb') as f:
                f.write(encrypted_content)
            
            file_model = FileModel(
                id=file_id,
                original_filename=filename,
                encrypted_filename=encrypted_filename,
                uploader_id=current_user.id,
                uploader_name=current_user.full_name or current_user.username,
                uploader_role='lawyer',
                recipient_id=request.form.get('recipient_id'),
                case_id=request.form.get('case_id'),
                description=request.form.get('description'),
                file_size=len(file_content),
                is_encrypted=True,
                encryption_key_a=5,
                encryption_key_b=8,
                uploaded_at=datetime.now()
            )
            db.session.add(file_model)
            db.session.commit()
            flash('File uploaded and encrypted successfully!', 'success')
            return redirect(url_for('lawyer_upload_files'))
        else:
            flash('Invalid file type', 'error')
    
    clients = UserModel.query.filter_by(role='client').all()
    all_cases = CaseModel.query.all()

    my_uploads = FileModel.query.filter_by(uploader_id=current_user.id).all()
    
    return render_template('lawyer/upload_files.html', 
                         clients=clients, 
                         cases=all_cases,
                         uploads=my_uploads)


@app.route('/lawyer/download-files')
@login_required
def lawyer_download_files():
    if current_user.role != 'lawyer':
        abort(403)
    available_files = FileModel.query.filter(
        or_(FileModel.uploader_id == current_user.id, FileModel.recipient_id == current_user.id, FileModel.uploader_role == 'client')
    ).all()

    return render_template('lawyer/download_files.html', files=available_files)


@app.route('/lawyer/schedule-consultations', methods=['GET', 'POST'])
@login_required
def lawyer_schedule_consultations():
    if current_user.role != 'lawyer':
        abort(403)
    
    if request.method == 'POST':
        appointment = AppointmentModel(
            id=generate_id(),
            lawyer_id=current_user.id,
            lawyer_name=current_user.full_name or current_user.username,
            client_id=request.form.get('client_id'),
            case_id=request.form.get('case_id'),
            appointment_date=request.form.get('appointment_date'),
            appointment_time=request.form.get('appointment_time'),
            appointment_type=request.form.get('appointment_type'),
            location=request.form.get('location'),
            notes=request.form.get('notes'),
            status='scheduled',
            created_at=datetime.now()
        )
        db.session.add(appointment)
        db.session.commit()
        flash('Consultation scheduled successfully!', 'success')
        return redirect(url_for('lawyer_schedule_consultations'))
    
    clients = UserModel.query.filter_by(role='client').all()
    all_cases = CaseModel.query.all()

    my_appointments = AppointmentModel.query.filter_by(lawyer_id=current_user.id).all()
    
    return render_template('lawyer/schedule_consultations.html', 
                         clients=clients, 
                         cases=all_cases,
                         appointments=my_appointments)


@app.route('/lawyer/court-info')
@login_required
def lawyer_court_info():
    if current_user.role != 'lawyer':
        abort(403)
    
    all_hearings = HearingModel.query.all()

    court_messages = MessageModel.query.filter(
        or_(MessageModel.recipient_id == current_user.id, MessageModel.recipient_role == 'lawyer')
    ).all()

    for msg in court_messages:
        if getattr(msg, 'is_encrypted', False) and getattr(msg, 'message', None):
            try:
                encrypted_bytes = base64.b64decode(msg.message)
                decrypted = affine_decrypt(encrypted_bytes)
                msg.decrypted_message = decrypted.decode('utf-8', errors='replace')
            except:
                msg.decrypted_message = '[Decryption failed]'

    return render_template('lawyer/court_info.html', 
                         hearings=all_hearings,
                         messages=court_messages)


@app.route('/client/dashboard')
@login_required
def client_dashboard():
    if current_user.role != 'client':
        abort(403)
    
    my_cases = CaseModel.query.filter_by(client_id=current_user.id).all()

    my_files = FileModel.query.filter(
        or_(FileModel.recipient_id == current_user.id, FileModel.uploader_id == current_user.id)
    ).all()

    my_appointments = AppointmentModel.query.filter_by(client_id=current_user.id).all()

    return render_template('client/dashboard.html', 
                         cases=my_cases,
                         files=my_files,
                         appointments=my_appointments)


@app.route('/client/case-status')
@login_required
def client_case_status():
    if current_user.role != 'client':
        abort(403)
    my_cases = CaseModel.query.filter_by(client_id=current_user.id).all()

    case_ids = [case.id for case in my_cases]
    my_hearings = HearingModel.query.filter(HearingModel.case_id.in_(case_ids)).all() if case_ids else []

    return render_template('client/case_status.html', cases=my_cases, hearings=my_hearings)


@app.route('/client/upload-documents', methods=['GET', 'POST'])
@login_required
def client_upload_documents():
    if current_user.role != 'client':
        abort(403)
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('client_upload_documents'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('client_upload_documents'))
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_id = generate_id()
            
            file_content = file.read()
            encrypted_content = affine_encrypt(file_content)
            
            encrypted_filename = f"enc_{file_id}_{filename}"
            encrypted_path = os.path.join(app.config['UPLOAD_FOLDER'], encrypted_filename)
            
            with open(encrypted_path, 'wb') as f:
                f.write(encrypted_content)
            
            file_model = FileModel(
                id=file_id,
                original_filename=filename,
                encrypted_filename=encrypted_filename,
                uploader_id=current_user.id,
                uploader_name=current_user.full_name or current_user.username,
                uploader_role='client',
                recipient_id=request.form.get('lawyer_id'),
                case_id=request.form.get('case_id'),
                description=request.form.get('description'),
                file_size=len(file_content),
                is_encrypted=True,
                encryption_key_a=5,
                encryption_key_b=8,
                uploaded_at=datetime.now()
            )
            db.session.add(file_model)
            db.session.commit()
            flash('Document uploaded and encrypted successfully!', 'success')
            return redirect(url_for('client_upload_documents'))
        else:
            flash('Invalid file type', 'error')
    
    lawyers = UserModel.query.filter_by(role='lawyer').all()

    my_cases = CaseModel.query.filter_by(client_id=current_user.id).all()

    my_uploads = FileModel.query.filter_by(uploader_id=current_user.id).all()
    
    return render_template('client/upload_documents.html', 
                         lawyers=lawyers, 
                         cases=my_cases,
                         uploads=my_uploads)


@app.route('/client/download-files')
@login_required
def client_download_files():
    if current_user.role != 'client':
        abort(403)
    available_files = FileModel.query.filter(
        or_(FileModel.recipient_id == current_user.id, FileModel.uploader_id == current_user.id)
    ).all()

    return render_template('client/download_files.html', files=available_files)


@app.route('/client/schedule-appointments', methods=['GET', 'POST'])
@login_required
def client_schedule_appointments():
    if current_user.role != 'client':
        abort(403)
    
    if request.method == 'POST':
        appointment = AppointmentModel(
            id=generate_id(),
            client_id=current_user.id,
            client_name=current_user.full_name or current_user.username,
            lawyer_id=request.form.get('lawyer_id'),
            case_id=request.form.get('case_id'),
            appointment_date=request.form.get('preferred_date') or request.form.get('appointment_date'),
            appointment_time=request.form.get('preferred_time') or request.form.get('appointment_time'),
            appointment_type=request.form.get('appointment_type'),
            notes=request.form.get('notes'),
            status='pending',
            created_at=datetime.now()
        )
        db.session.add(appointment)
        db.session.commit()
        flash('Appointment request submitted!', 'success')
        return redirect(url_for('client_schedule_appointments'))
    
    lawyers = UserModel.query.filter_by(role='lawyer').all()

    my_cases = CaseModel.query.filter_by(client_id=current_user.id).all()

    my_appointments = AppointmentModel.query.filter_by(client_id=current_user.id).all()
    
    return render_template('client/schedule_appointments.html', 
                         lawyers=lawyers, 
                         cases=my_cases,
                         appointments=my_appointments)


@app.route('/client/hearing-dates')
@login_required
def client_hearing_dates():
    if current_user.role != 'client':
        abort(403)
    
    my_cases = CaseModel.query.filter_by(client_id=current_user.id).all()
    case_ids = [case.id for case in my_cases]

    my_hearings = HearingModel.query.filter(HearingModel.case_id.in_(case_ids)).all() if case_ids else []

    return render_template('client/hearing_dates.html', hearings=my_hearings, cases=my_cases)


@app.route('/download/encrypted/<file_id>')
@login_required
def download_encrypted(file_id):
    file_data = FileModel.query.filter_by(id=file_id).first()
    
    if not file_data:
        flash('File not found', 'error')
        return redirect(url_for('index'))
    
    if current_user.id != file_data.uploader_id and current_user.id != getattr(file_data, 'recipient_id', None):
        if current_user.role != 'court':
            abort(403)

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_data.encrypted_filename)
    
    if not os.path.exists(file_path):
        flash('File not found on server', 'error')
        return redirect(url_for('index'))
    
    return send_file(file_path, 
                    as_attachment=True, 
                    download_name=f"encrypted_{file_data.original_filename}")


@app.route('/download/decrypted/<file_id>')
@login_required
def download_decrypted(file_id):
    file_data = FileModel.query.filter_by(id=file_id).first()
    
    if not file_data:
        flash('File not found', 'error')
        return redirect(url_for('index'))
    
    if current_user.id != file_data.uploader_id and current_user.id != getattr(file_data, 'recipient_id', None):
        if current_user.role != 'court':
            abort(403)

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_data.encrypted_filename)
    
    if not os.path.exists(file_path):
        flash('File not found on server', 'error')
        return redirect(url_for('index'))
    
    with open(file_path, 'rb') as f:
        encrypted_content = f.read()
    
    try:
        decrypted_content = affine_decrypt(
            encrypted_content, 
            getattr(file_data, 'encryption_key_a', 5),
            getattr(file_data, 'encryption_key_b', 8)
        )
    except Exception as e:
        flash(f'Decryption failed: {str(e)}', 'error')
        return redirect(url_for('index'))
    
    import io
    return send_file(
        io.BytesIO(decrypted_content),
        as_attachment=True,
        download_name=file_data.original_filename
    )


@app.route('/decrypt-message/<message_id>')
@login_required
def decrypt_message(message_id):
    message = MessageModel.query.filter_by(id=message_id).first()
    if not message:
        return jsonify({'error': 'Message not found'}), 404

    if getattr(message, 'is_encrypted', False):
        try:
            encrypted_bytes = base64.b64decode(message.message)
            decrypted = affine_decrypt(encrypted_bytes)
            return jsonify({'decrypted': decrypted.decode('utf-8', errors='replace')})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return jsonify({'decrypted': message.message})
