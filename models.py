from app import app
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
import datetime

db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(15), unique=True, nullable=True)  # New phone number field
    role = db.Column(db.String(50), nullable=False)  # 'Admin', 'Customer', 'Service Professional'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    

    # One-to-One relationships
    customer_ref = db.relationship('Customer', back_populates='user_ref', uselist=False)
    service_professional_ref = db.relationship('ServiceProfessional', back_populates='user_ref', uselist=False)

# Admin Model
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user_ref = db.relationship('User', backref='admin_ref', uselist=False)

# Customer Model
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    address = db.Column(db.String(255), nullable=True)
    pin_code = db.Column(db.String(10), nullable=True)
    user_ref = db.relationship('User', back_populates='customer_ref')


    # Relationships
    user = db.relationship('User', backref='customer')
    # One-to-Many relationship with ServiceRequest
    service_requests = db.relationship('ServiceRequest', back_populates='customer_ref')

# Service Professional Model
class ServiceProfessional(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    service_type = db.Column(db.String(120), nullable=False)
    experience = db.Column(db.Float, nullable=False)
    rating = db.Column(db.Float, default=0.0)
    resume_filename = db.Column(db.String(255), nullable=True)  # For storing resume file name
    address = db.Column(db.String(255), nullable=True)  # Address of the service professional
    pin_code = db.Column(db.String(10), nullable=True)  # Pin code (postal code)
    description = db.Column(db.String(255), nullable=True)
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    user_ref = db.relationship('User', back_populates='service_professional_ref')

    # Virtual column to get the name from the associated user
    @property
    def name(self):
        return self.user_ref.username


    # Relationships
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    service_ref = db.relationship('Service', back_populates='service_professionals')
    service_requests = db.relationship('ServiceRequest', back_populates='service_professional_ref')

# Service Model
class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    service_professionals = db.relationship('ServiceProfessional', back_populates='service_ref')
    service_requests = db.relationship('ServiceRequest', back_populates='service_ref')
    

# Service Request Model
class ServiceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('service_professional.id'))
    date_of_request = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    date_of_completion = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(50), default='requested')      # requested/accepted/closed
    remarks = db.Column(db.String(255), nullable=True)

    # Relationships
    service_ref = db.relationship('Service', back_populates='service_requests')
    customer_ref = db.relationship('Customer', back_populates='service_requests')
    service_professional_ref = db.relationship('ServiceProfessional', back_populates='service_requests')

    # Properties to fetch customer details
    @property
    def customer_name(self):
        return self.customer_ref.user.username if self.customer_ref else None

    @property
    def customer_contact(self):
        return self.customer_ref.user.phone_number if self.customer_ref else None

    @property
    def customer_address(self):
        return self.customer_ref.address if self.customer_ref else None

    @property
    def customer_pincode(self):
        return self.customer_ref.pin_code if self.customer_ref else None

# Review Model
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_request_id = db.Column(db.Integer, db.ForeignKey('service_request.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # Rating out of 5
    comment = db.Column(db.String(255), nullable=True)

    service_request_ref = db.relationship('ServiceRequest', backref='reviews')
    customer_ref = db.relationship('Customer', backref='reviews')

# Admin Initialization
def create_admin():
    # Check if there's already an admin user
    admin_user = User.query.filter_by(role='admin').first()
    if not admin_user:
        # Create a new User object for the admin
        hashed_password = generate_password_hash('admin')
        admin_user = User(username='admin', password_hash=hashed_password, email='admin@example.com', role='admin')
        db.session.add(admin_user)
        db.session.commit()  # Commit to get the admin_user ID

        # Now create an Admin object associated with the created user
        admin = Admin(user_id=admin_user.id)
        db.session.add(admin)
        db.session.commit()  # Commit the Admin object

        print("Admin created successfully!")
    else:
        print("Admin already exists.")


try:
    with app.app_context():
        db.create_all()
        create_admin()
except Exception as e:
    print(f"Error creating database or admin user: {e}")
