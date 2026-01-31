"""
Children's Hospital Website
Complete solution with Flask backend, departments, and user-friendly interface
"""

import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import base64
from PIL import Image, ImageDraw, ImageFont
import io

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'children_hospital_secret_key_2023'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    appointments = db.relationship('Appointment', backref='user', lazy=True)
    medical_records = db.relationship('MedicalRecord', backref='user', lazy=True)

class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(50), nullable=False)
    services = db.Column(db.Text)  # JSON string of services
    doctors_count = db.Column(db.Integer, default=0)
    contact_ext = db.Column(db.String(10))
    
    # Relationships
    doctors = db.relationship('Doctor', backref='department', lazy=True)

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    experience = db.Column(db.Integer)  # Years of experience
    qualification = db.Column(db.String(200))
    availability = db.Column(db.String(200))  # JSON string of available slots
    contact = db.Column(db.String(50))
    photo_url = db.Column(db.String(200))

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    child_name = db.Column(db.String(100), nullable=False)
    child_age = db.Column(db.Integer, nullable=False)
    appointment_date = db.Column(db.DateTime, nullable=False)
    symptoms = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    doctor = db.relationship('Doctor', backref='appointments', lazy=True)
    department = db.relationship('Department', backref='appointments', lazy=True)

class MedicalRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    record_type = db.Column(db.String(50), nullable=False)  # prescription, test_result, diagnosis
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    doctor_name = db.Column(db.String(100))
    date = db.Column(db.DateTime, nullable=False)
    file_url = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    category = db.Column(db.String(50))  # syrup, tablet, injection, etc.
    for_age = db.Column(db.String(50))  # age group

# Create database tables
with app.app_context():
    db.create_all()

# Hospital Departments Data
DEPARTMENTS_DATA = [
    {
        'name': 'Pediatric Emergency',
        'description': '24/7 emergency care for children with critical conditions',
        'icon': 'emergency',
        'services': ['Trauma Care', 'Critical Care', 'Emergency Surgery', 'Resuscitation'],
        'doctors_count': 8,
        'contact_ext': '101'
    },
    {
        'name': 'Neonatology',
        'description': 'Specialized care for newborn babies, especially premature or ill newborns',
        'icon': 'baby',
        'services': ['NICU', 'Premature Baby Care', 'Newborn Screening', 'Breastfeeding Support'],
        'doctors_count': 6,
        'contact_ext': '102'
    },
    {
        'name': 'Pediatric Cardiology',
        'description': 'Diagnosis and treatment of heart conditions in children',
        'icon': 'heart',
        'services': ['Echocardiography', 'Cardiac Surgery', 'ECG Monitoring', 'Heart Rehabilitation'],
        'doctors_count': 5,
        'contact_ext': '103'
    },
    {
        'name': 'Pediatric Oncology',
        'description': 'Comprehensive cancer care for children',
        'icon': 'stethoscope',
        'services': ['Chemotherapy', 'Radiation Therapy', 'Bone Marrow Transplant', 'Palliative Care'],
        'doctors_count': 7,
        'contact_ext': '104'
    },
    {
        'name': 'Pediatric Neurology',
        'description': 'Treatment of neurological disorders in children',
        'icon': 'brain',
        'services': ['EEG Monitoring', 'Epilepsy Management', 'Neurological Surgery', 'Developmental Assessment'],
        'doctors_count': 5,
        'contact_ext': '105'
    },
    {
        'name': 'Pediatric Surgery',
        'description': 'Surgical procedures for children from birth to adolescence',
        'icon': 'surgery',
        'services': ['General Surgery', 'Minimally Invasive Surgery', 'Trauma Surgery', 'Post-operative Care'],
        'doctors_count': 6,
        'contact_ext': '106'
    },
    {
        'name': 'Pediatric Dentistry',
        'description': 'Dental care specifically for children',
        'icon': 'tooth',
        'services': ['Dental Checkups', 'Orthodontics', 'Tooth Extraction', 'Dental Hygiene Education'],
        'doctors_count': 4,
        'contact_ext': '107'
    },
    {
        'name': 'Child Psychology',
        'description': 'Mental health and behavioral support for children',
        'icon': 'mind',
        'services': ['Behavioral Therapy', 'Cognitive Therapy', 'Family Counseling', 'Autism Support'],
        'doctors_count': 5,
        'contact_ext': '108'
    }
]

# Function to create hospital logo
def create_hospital_logo_svg():
    """Generate hospital logo as SVG"""
    svg_logo = '''
    <svg width="400" height="200" xmlns="http://www.w3.org/2000/svg">
        <rect width="400" height="200" fill="white"/>
        <!-- Hospital Building -->
        <polygon points="100,120 150,80 200,120" fill="lightblue"/>
        <rect x="100" y="120" width="100" height="60" fill="lightblue"/>
        <!-- Medical Cross -->
        <rect x="145" y="90" width="10" height="40" fill="red"/>
        <rect x="130" y="105" width="40" height="10" fill="red"/>
        <!-- Heart -->
        <circle cx="230" cy="90" r="10" fill="pink"/>
        <circle cx="250" cy="90" r="10" fill="pink"/>
        <polygon points="230,90 270,90 250,130" fill="pink"/>
        <!-- Text -->
        <text x="280" y="70" font-family="Arial" font-size="24" fill="orange">Sunshine</text>
        <text x="280" y="100" font-family="Arial" font-size="24" fill="blue">Children's</text>
        <text x="280" y="130" font-family="Arial" font-size="24" fill="green">Hospital</text>
    </svg>
    '''
    # Convert to base64 for HTML embedding
    svg_bytes = svg_logo.encode('utf-8')
    base64_svg = base64.b64encode(svg_bytes).decode('utf-8')
    return f"data:image/svg+xml;base64,{base64_svg}"

# Use this function instead of the Pillow one
def create_hospital_logo():
    return create_hospital_logo_svg()
# Initialize data in database
def initialize_data():
    """Initialize the database with sample data"""
    with app.app_context():
        # Check if departments already exist
        if Department.query.count() == 0:
            for dept_data in DEPARTMENTS_DATA:
                dept = Department(
                    name=dept_data['name'],
                    description=dept_data['description'],
                    icon=dept_data['icon'],
                    services=json.dumps(dept_data['services']),
                    doctors_count=dept_data['doctors_count'],
                    contact_ext=dept_data['contact_ext']
                )
                db.session.add(dept)
            
            # Add sample doctors
            doctors_data = [
                {'name': 'Dr. Sarah Johnson', 'specialization': 'Pediatric Emergency', 'department_id': 1, 'experience': 15},
                {'name': 'Dr. Michael Chen', 'specialization': 'Neonatology', 'department_id': 2, 'experience': 12},
                {'name': 'Dr. Emily Rodriguez', 'specialization': 'Pediatric Cardiology', 'department_id': 3, 'experience': 18},
                {'name': 'Dr. David Kim', 'specialization': 'Pediatric Oncology', 'department_id': 4, 'experience': 20},
                {'name': 'Dr. Lisa Wang', 'specialization': 'Pediatric Neurology', 'department_id': 5, 'experience': 14},
                {'name': 'Dr. Robert Miller', 'specialization': 'Pediatric Surgery', 'department_id': 6, 'experience': 16},
                {'name': 'Dr. Maria Garcia', 'specialization': 'Pediatric Dentistry', 'department_id': 7, 'experience': 10},
                {'name': 'Dr. James Wilson', 'specialization': 'Child Psychology', 'department_id': 8, 'experience': 13},
            ]
            
            for doc_data in doctors_data:
                doctor = Doctor(**doc_data)
                db.session.add(doctor)
            
            # Add sample medicines
            medicines = [
                {'name': 'Children\'s Paracetamol Syrup', 'description': 'Fever and pain relief for children', 'price': 8.99, 'stock': 50, 'category': 'syrup', 'for_age': '2-12 years'},
                {'name': 'Amoxicillin Suspension', 'description': 'Antibiotic for bacterial infections', 'price': 12.50, 'stock': 30, 'category': 'syrup', 'for_age': '1-10 years'},
                {'name': 'Pediatric Multivitamin', 'description': 'Essential vitamins for child development', 'price': 15.75, 'stock': 40, 'category': 'tablet', 'for_age': '4+ years'},
                {'name': 'Salbutamol Inhaler', 'description': 'For asthma and breathing difficulties', 'price': 25.00, 'stock': 20, 'category': 'inhaler', 'for_age': '5+ years'},
            ]
            
            for med_data in medicines:
                medicine = Medicine(**med_data)
                db.session.add(medicine)
            
            db.session.commit()
            print("Database initialized with sample data")

# Routes
@app.route('/')
def index():
    """Home page"""
    logo_data = create_hospital_logo()
    departments = Department.query.all()
    
    # Get statistics
    total_doctors = sum(dept.doctors_count for dept in departments)
    total_departments = len(departments)
    
    return render_template('index.html', 
                         logo_data=logo_data, 
                         departments=departments,
                         total_doctors=total_doctors,
                         total_departments=total_departments)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register'))
        
        # Create new user
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    """User dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    appointments = Appointment.query.filter_by(user_id=user.id).order_by(Appointment.appointment_date.desc()).limit(5).all()
    records = MedicalRecord.query.filter_by(user_id=user.id).order_by(MedicalRecord.date.desc()).limit(5).all()
    
    return render_template('dashboard.html', 
                         user=user, 
                         appointments=appointments, 
                         records=records)

@app.route('/departments')
def departments():
    """All departments page"""
    departments = Department.query.all()
    return render_template('departments.html', departments=departments)

@app.route('/department/<int:dept_id>')
def department_detail(dept_id):
    """Department detail page"""
    department = Department.query.get_or_404(dept_id)
    doctors = Doctor.query.filter_by(department_id=dept_id).all()
    services = json.loads(department.services) if department.services else []
    
    return render_template('department_detail.html', 
                         department=department, 
                         doctors=doctors, 
                         services=services)

@app.route('/doctors')
def doctors():
    """All doctors page"""
    doctors = Doctor.query.all()
    departments = Department.query.all()
    
    return render_template('doctors.html', doctors=doctors, departments=departments)

@app.route('/book_appointment', methods=['GET', 'POST'])
def book_appointment():
    """Book appointment page"""
    if 'user_id' not in session:
        flash('Please login to book an appointment', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        doctor_id = request.form['doctor_id']
        child_name = request.form['child_name']
        child_age = request.form['child_age']
        appointment_date = request.form['appointment_date']
        symptoms = request.form.get('symptoms', '')
        
        doctor = Doctor.query.get(doctor_id)
        
        appointment = Appointment(
            user_id=session['user_id'],
            doctor_id=doctor_id,
            department_id=doctor.department_id,
            child_name=child_name,
            child_age=child_age,
            appointment_date=datetime.strptime(appointment_date, '%Y-%m-%dT%H:%M'),
            symptoms=symptoms
        )
        
        db.session.add(appointment)
        db.session.commit()
        
        flash('Appointment booked successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    # GET request - show form
    doctors = Doctor.query.all()
    return render_template('book_appointment.html', doctors=doctors)

@app.route('/pharmacy')
def pharmacy():
    """Online pharmacy"""
    medicines = Medicine.query.filter(Medicine.stock > 0).all()
    categories = db.session.query(Medicine.category).distinct().all()
    
    return render_template('pharmacy.html', medicines=medicines, categories=categories)

@app.route('/medical_records')
def medical_records():
    """User's medical records"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    records = MedicalRecord.query.filter_by(user_id=session['user_id']).order_by(MedicalRecord.date.desc()).all()
    
    return render_template('medical_records.html', records=records)

@app.route('/emergency')
def emergency():
    """Emergency information page"""
    return render_template('emergency.html')

# API endpoints
@app.route('/api/departments')
def api_departments():
    """API endpoint for departments"""
    departments = Department.query.all()
    result = []
    
    for dept in departments:
        result.append({
            'id': dept.id,
            'name': dept.name,
            'description': dept.description,
            'doctors_count': dept.doctors_count,
            'contact_ext': dept.contact_ext
        })
    
    return jsonify(result)

@app.route('/api/doctors/<int:dept_id>')
def api_doctors_by_department(dept_id):
    """API endpoint for doctors by department"""
    doctors = Doctor.query.filter_by(department_id=dept_id).all()
    result = []
    
    for doctor in doctors:
        result.append({
            'id': doctor.id,
            'name': doctor.name,
            'specialization': doctor.specialization,
            'experience': doctor.experience,
            'qualification': doctor.qualification
        })
    
    return jsonify(result)

@app.route('/api/appointments')
def api_appointments():
    """API endpoint for user's appointments"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    appointments = Appointment.query.filter_by(user_id=session['user_id']).all()
    result = []
    
    for appt in appointments:
        result.append({
            'id': appt.id,
            'child_name': appt.child_name,
            'doctor_name': appt.doctor.name,
            'department': appt.department.name,
            'date': appt.appointment_date.strftime('%Y-%m-%d %H:%M'),
            'status': appt.status
        })
    
    return jsonify(result)

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# Templates (HTML embedded in Python for simplicity)
# In a real application, these would be separate HTML files

def create_templates():
    """Create HTML templates directory and files"""
    templates_dir = 'templates'
    os.makedirs(templates_dir, exist_ok=True)
    
    # Create base template
    base_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sunshine Children's Hospital - {% block title %}{% endblock %}</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            :root {
                --primary: #4a9eff;
                --secondary: #ff9a56;
                --accent: #7b68ee;
                --light: #f0f8ff;
                --dark: #2c3e50;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f8f9fa;
            }
            
            .navbar-brand {
                font-weight: bold;
                color: var(--primary) !important;
            }
            
            .btn-primary {
                background-color: var(--primary);
                border-color: var(--primary);
            }
            
            .btn-warning {
                background-color: var(--secondary);
                border-color: var(--secondary);
                color: white;
            }
            
            .hospital-header {
                background: linear-gradient(135deg, var(--primary), var(--accent));
                color: white;
                padding: 60px 0;
                margin-bottom: 30px;
            }
            
            .department-card {
                border: none;
                border-radius: 15px;
                transition: transform 0.3s;
                margin-bottom: 20px;
            }
            
            .department-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            }
            
            .icon-circle {
                width: 70px;
                height: 70px;
                border-radius: 50%;
                background-color: var(--light);
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 15px;
            }
            
            .emergency-banner {
                background-color: #ff6b6b;
                color: white;
                padding: 15px;
                border-radius: 10px;
                margin: 20px 0;
                animation: pulse 2s infinite;
            }
            
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.8; }
                100% { opacity: 1; }
            }
            
            .footer {
                background-color: var(--dark);
                color: white;
                padding: 40px 0;
                margin-top: 50px;
            }
        </style>
    </head>
    <body>
        <!-- Navigation -->
        <nav class="navbar navbar-expand-lg navbar-light bg-white shadow-sm">
            <div class="container">
                <a class="navbar-brand" href="/">
                    <i class="fas fa-heartbeat me-2"></i>
                    Sunshine Children's Hospital
                </a>
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav ms-auto">
                        <li class="nav-item"><a class="nav-link" href="/">Home</a></li>
                        <li class="nav-item"><a class="nav-link" href="/departments">Departments</a></li>
                        <li class="nav-item"><a class="nav-link" href="/doctors">Doctors</a></li>
                        <li class="nav-item"><a class="nav-link" href="/pharmacy">Pharmacy</a></li>
                        {% if 'user_id' in session %}
                            <li class="nav-item"><a class="nav-link" href="/dashboard">Dashboard</a></li>
                            <li class="nav-item"><a class="nav-link" href="/logout">Logout ({{ session.username }})</a></li>
                        {% else %}
                            <li class="nav-item"><a class="nav-link" href="/login">Login</a></li>
                            <li class="nav-item"><a class="nav-link" href="/register">Register</a></li>
                        {% endif %}
                    </ul>
                </div>
            </div>
        </nav>
        
        <!-- Flash Messages -->
        <div class="container mt-3">
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }} alert-dismissible fade show">
                            {{ message }}
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
        </div>
        
        <!-- Main Content -->
        {% block content %}{% endblock %}
        
        <!-- Footer -->
        <footer class="footer">
            <div class="container">
                <div class="row">
                    <div class="col-md-4">
                        <h5>Sunshine Children's Hospital</h5>
                        <p>Providing compassionate care for children since 1995</p>
                        <img src="{{ logo_data }}" alt="Hospital Logo" style="max-width: 200px; background: white; padding: 10px; border-radius: 10px;">
                    </div>
                    <div class="col-md-4">
                        <h5>Quick Links</h5>
                        <ul class="list-unstyled">
                            <li><a href="/departments" class="text-light">Departments</a></li>
                            <li><a href="/doctors" class="text-light">Find a Doctor</a></li>
                            <li><a href="/pharmacy" class="text-light">Online Pharmacy</a></li>
                            <li><a href="/emergency" class="text-light">Emergency Info</a></li>
                        </ul>
                    </div>
                    <div class="col-md-4">
                        <h5>Contact Us</h5>
                        <p><i class="fas fa-phone me-2"></i> Emergency: 1-800-123-4567</p>
                        <p><i class="fas fa-envelope me-2"></i> info@sunshinechildrenshospital.org</p>
                        <p><i class="fas fa-map-marker-alt me-2"></i> 123 Health Street, Medical City</p>
                    </div>
                </div>
                <hr class="bg-light">
                <div class="text-center">
                    <p>&copy; 2023 Sunshine Children's Hospital. All rights reserved.</p>
                </div>
            </div>
        </footer>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            // Auto-dismiss alerts after 5 seconds
            setTimeout(function() {
                var alerts = document.querySelectorAll('.alert');
                alerts.forEach(function(alert) {
                    var bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                });
            }, 5000);
        </script>
        {% block scripts %}{% endblock %}
    </body>
    </html>
    '''
    
    # Home page template
    index_template = '''
    {% extends "base.html" %}
    {% block title %}Home{% endblock %}
    {% block content %}
    <div class="hospital-header text-center">
        <div class="container">
            <h1 class="display-4">Welcome to Sunshine Children's Hospital</h1>
            <p class="lead">Where every child matters and every smile counts</p>
            <a href="/departments" class="btn btn-warning btn-lg mt-3">
                <i class="fas fa-stethoscope me-2"></i>Explore Our Departments
            </a>
        </div>
    </div>
    
    <div class="container">
        <!-- Emergency Banner -->
        <div class="emergency-banner text-center">
            <h4><i class="fas fa-ambulance me-2"></i>24/7 Emergency Services Available</h4>
            <p class="mb-0">Call 1-800-123-4567 for immediate assistance</p>
        </div>
        
        <!-- Quick Stats -->
        <div class="row text-center mb-5">
            <div class="col-md-4">
                <div class="p-4 bg-white rounded shadow">
                    <h2 class="text-primary">{{ total_departments }}+</h2>
                    <p>Specialized Departments</p>
                </div>
            </div>
            <div class="col-md-4">
                <div class="p-4 bg-white rounded shadow">
                    <h2 class="text-primary">{{ total_doctors }}+</h2>
                    <p>Expert Doctors</p>
                </div>
            </div>
            <div class="col-md-4">
                <div class="p-4 bg-white rounded shadow">
                    <h2 class="text-primary">24/7</h2>
                    <p>Emergency Care</p>
                </div>
            </div>
        </div>
        
        <!-- Featured Departments -->
        <h2 class="text-center mb-4">Our Specialized Departments</h2>
        <div class="row">
            {% for department in departments[:4] %}
            <div class="col-md-3">
                <div class="card department-card">
                    <div class="card-body text-center">
                        <div class="icon-circle">
                            <i class="fas fa-{% if department.icon == 'emergency' %}ambulance{% elif department.icon == 'baby' %}baby{% elif department.icon == 'heart' %}heartbeat{% elif department.icon == 'surgery' %}user-md{% elif department.icon == 'tooth' %}tooth{% elif department.icon == 'mind' %}brain{% else %}stethoscope{% endif %} fa-2x text-primary"></i>
                        </div>
                        <h5>{{ department.name }}</h5>
                        <p class="text-muted small">{{ department.description[:80] }}...</p>
                        <a href="/department/{{ department.id }}" class="btn btn-outline-primary btn-sm">Learn More</a>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        
        <!-- Quick Actions -->
        <div class="row mt-5">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h4><i class="fas fa-calendar-check text-primary me-2"></i>Book Appointment</h4>
                        <p>Schedule a visit with our specialist doctors</p>
                        <a href="/book_appointment" class="btn btn-primary">Book Now</a>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h4><i class="fas fa-pills text-primary me-2"></i>Online Pharmacy</h4>
                        <p>Order medicines online with home delivery</p>
                        <a href="/pharmacy" class="btn btn-primary">Order Now</a>
                    </div>
                </div>
            </div>
        </div>
    </div>
    {% endblock %}
    '''
    
    # Departments page template
    departments_template = '''
    {% extends "base.html" %}
    {% block title %}Departments{% endblock %}
    {% block content %}
    <div class="container py-5">
        <h1 class="text-center mb-5">Our Specialized Departments</h1>
        
        <div class="row">
            {% for department in departments %}
            <div class="col-md-6 mb-4">
                <div class="card department-card h-100">
                    <div class="card-body">
                        <div class="d-flex">
                            <div class="me-3">
                                <div class="icon-circle">
                                    <i class="fas fa-{% if department.icon == 'emergency' %}ambulance{% elif department.icon == 'baby' %}baby{% elif department.icon == 'heart' %}heartbeat{% elif department.icon == 'surgery' %}user-md{% elif department.icon == 'tooth' %}tooth{% elif department.icon == 'mind' %}brain{% else %}stethoscope{% endif %} fa-2x text-primary"></i>
                                </div>
                            </div>
                            <div>
                                <h4>{{ department.name }}</h4>
                                <p>{{ department.description }}</p>
                                <div class="d-flex justify-content-between align-items-center">
                                    <span class="badge bg-primary">{{ department.doctors_count }} Doctors</span>
                                    <div>
                                        <span class="me-3">Ext: {{ department.contact_ext }}</span>
                                        <a href="/department/{{ department.id }}" class="btn btn-primary btn-sm">View Details</a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
    {% endblock %}
    '''
    
    # Write templates to files
    templates = {
        'base.html': base_template,
        'index.html': index_template,
        'departments.html': departments_template,
        # Add more templates as needed...
    }
    
    for filename, content in templates.items():
        with open(os.path.join(templates_dir, filename), 'w') as f:
            f.write(content)

# Run the application
if __name__ == '__main__':
    # Create templates directory
    create_templates()
    
    # Initialize database with sample data
    initialize_data()
    
    # Generate hospital logo
    logo = create_hospital_logo()
    print("Hospital logo generated successfully!")
    
    # Run the Flask app
    print("\n" + "="*50)
    print("Sunshine Children's Hospital Website")
    print("="*50)
    print("\nAccess the website at: http://127.0.0.1:5000")
    print("\nFeatures:")
    print("- User Registration & Login")
    print("- Department Information")
    print("- Doctor Directory")
    print("- Appointment Booking")
    print("- Online Pharmacy")
    print("- Medical Records")
    print("- Emergency Information")
    print("\nAdmin account: admin / admin123")
    print("="*50)
    
    # Create admin user
    with app.app_context():
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@hospital.org',
                password=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created: admin / admin123")
    
    app.run(debug=True, port=5000)