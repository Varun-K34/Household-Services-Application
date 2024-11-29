from flask import Flask, render_template, request, redirect, url_for, flash, session
from app import app
from models import db, User, Service, ServiceRequest, Review
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime

# ----------------------------------------------
# Authentication Endpoints (4)
# ----------------------------------------------

@app.route("/")
def home():
    return render_template("login.html")

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role')  # 'customer' or 'professional'

        if not username or not password or not confirm_password:
            flash('Please fill out all fields')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash('Invalid username or password')
            return redirect(url_for('login'))

        session['user_id'] = user.id
        session['role'] = user.role
        flash('Login successful')
        
        # Redirect based on user role
        if user.role == 'admin':
            return redirect(url_for('admin_dashboard'))  # Admin Dashboard
        elif user.role == 'professional':
            return redirect(url_for('professional_dashboard'))  # Professional Dashboard
        else:
            return redirect(url_for('customer_dashboard'))  # Customer Dashboard

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out')
    return redirect(url_for('login'))

# ----------------------------------------------
# Admin Dashboard Endpoints (7)
# ----------------------------------------------

@app.route('/dashboard')
def dashboard():
    if 'role' not in session or session['role'] != 'admin':
        flash('Unauthorized access. You must be logged in as an admin to view this page.', 'danger')
        return redirect(url_for('login'))

    # Fetch data related to users and services
    users = User.query.all()
    services = Service.query.all()

    return render_template('admin/dashboard.html', users=users, services=services)


@app.route('/admin/approve/<int:user_id>', methods=["POST"])
def approve_professional(user_id):
    if 'role' not in session or session['role'] != 'admin':
        flash('Unauthorized access')
        return redirect(url_for('login'))

    user = User.query.get(user_id)
    if not user or user.role != 'professional':
        flash('Invalid user')
        return redirect(url_for('dashboard'))

    user.is_approved = True
    db.session.commit()
    flash('Professional approved')
    return redirect(url_for('dashboard'))

@app.route('/admin/block/<int:user_id>', methods=["POST"])
def block_user(user_id):
    if 'role' not in session or session['role'] != 'admin':
        flash('Unauthorized access')
        return redirect(url_for('login'))

    user = User.query.get(user_id)
    user.is_active = False
    db.session.commit()
    flash('User blocked')
    return redirect(url_for('dashboard'))

@app.route('/admin/unblock/<int:user_id>', methods=["POST"])
def unblock_user(user_id):
    if 'role' not in session or session['role'] != 'admin':
        flash('Unauthorized access')
        return redirect(url_for('login'))

    user = User.query.get(user_id)
    user.is_active = True
    db.session.commit()
    flash('User unblocked')
    return redirect(url_for('dashboard'))

@app.route('/service/add', methods=["GET", "POST"])
def add_service():
    if request.method == "POST":
        name = request.form.get('name')
        description = request.form.get('description')

        if not name or not description:
            flash('Please fill out all fields')
            return redirect(url_for('add_service'))

        service = Service(name=name, description=description)
        db.session.add(service)
        db.session.commit()
        flash('Service added successfully')
        return redirect(url_for('dashboard'))

    return render_template('admin/add_service.html')

@app.route('/service/<int:service_id>/edit', methods=["GET", "POST"])
def edit_service(service_id):
    service = Service.query.get(service_id)
    if request.method == "POST":
        service.name = request.form.get('name')
        service.description = request.form.get('description')
        db.session.commit()
        flash('Service updated successfully')
        return redirect(url_for('dashboard'))

    return render_template('admin/edit_service.html', service=service)

@app.route('/service/<int:service_id>/delete', methods=["POST"])
def delete_service(service_id):
    service = Service.query.get(service_id)
    db.session.delete(service)
    db.session.commit()
    flash('Service deleted successfully')
    return redirect(url_for('dashboard'))

# ----------------------------------------------
# Customer Actions Endpoints (4)
# ----------------------------------------------

@app.route('/customer_dashboard')
def customer_dashboard():
    if 'role' not in session or session['role'] != 'customer':
        flash('Unauthorized access. You must be logged in as a customer to view this page.', 'danger')
        return redirect(url_for('login'))

    # Fetch any data specific to the customer, e.g., their service requests or booking history
    service_requests = ServiceRequest.query.filter_by(customer_id=session['user_id']).all()
    return render_template('customer/dashboard.html', service_requests=service_requests)


@app.route('/services')
def services():
    services = Service.query.all()
    return render_template('customer/services.html', services=services)

@app.route('/service_request/<int:service_id>', methods=["GET", "POST"])
def service_request(service_id):
    if request.method == "POST":
        description = request.form.get('description')
        service_request = ServiceRequest(
            customer_id=session['user_id'], 
            service_id=service_id, 
            description=description, 
            status='Pending'
        )
        db.session.add(service_request)
        db.session.commit()
        flash('Service request created successfully')
        return redirect(url_for('services'))

    service = Service.query.get(service_id)
    return render_template('customer/service_request.html', service=service)

@app.route('/my_requests')
def my_requests():
    requests = ServiceRequest.query.filter_by(customer_id=session['user_id']).all()
    return render_template('customer/my_requests.html', requests=requests)

@app.route('/cancel_request/<int:request_id>', methods=["POST"])
def cancel_request(request_id):
    request = ServiceRequest.query.get(request_id)
    db.session.delete(request)
    db.session.commit()
    flash('Request canceled successfully')
    return redirect(url_for('my_requests'))

# ----------------------------------------------
# Service Professional Actions Endpoints (4)
# ----------------------------------------------

@app.route('/professional_dashboard')
def professional_dashboard():
    if 'role' not in session or session['role'] != 'professional':
        flash('Unauthorized access. You must be logged in as a professional to view this page.', 'danger')
        return redirect(url_for('login'))

    # Fetch any data specific to the professional, e.g., pending service requests
    pending_requests = ServiceRequest.query.filter_by(professional_id=session['user_id'], status='pending').all()
    return render_template('professional/dashboard.html', pending_requests=pending_requests)


@app.route('/requests')
def view_requests():
    requests = ServiceRequest.query.filter_by(professional_id=None).all()
    return render_template('professional/requests.html', requests=requests)

@app.route('/accept_request/<int:request_id>', methods=["POST"])
def accept_request(request_id):
    request = ServiceRequest.query.get(request_id)
    request.professional_id = session['user_id']
    request.status = 'Accepted'
    db.session.commit()
    flash('Request accepted')
    return redirect(url_for('view_requests'))

@app.route('/complete_request/<int:request_id>', methods=["POST"])
def complete_request(request_id):
    request = ServiceRequest.query.get(request_id)
    request.status = 'Completed'
    db.session.commit()
    flash('Request marked as completed')
    return redirect(url_for('view_requests'))

@app.route('/my_jobs')
def my_jobs():
    jobs = ServiceRequest.query.filter_by(professional_id=session['user_id']).all()
    return render_template('professional/my_jobs.html', jobs=jobs)

# ----------------------------------------------
# Reviews Endpoints (2)
# ----------------------------------------------

@app.route('/submit_review/<int:service_id>', methods=['POST'])
def submit_review(service_id):
    # Get data from form
    rating = request.form.get('rating')
    comment = request.form.get('comment')

    if not rating or not comment:
        flash("Please fill out all fields")
        return redirect(url_for('view_reviews', service_id=service_id))

    # Create and store the review
    review = Review(service_id=service_id, rating=rating, comment=comment, customer_id=session['user.roll_no'])
    db.session.add(review)
    db.session.commit()

    flash("Review submitted successfully")
    return redirect(url_for('view_reviews', service_id=service_id))

@app.route('/reviews/<int:service_id>', methods=['GET'])
def view_reviews(service_id):
    # Fetch the reviews for a specific service
    reviews = Review.query.filter_by(service_id=service_id).all()
    
    if not reviews:
        flash("No reviews found for this service.")
        return redirect(url_for('search_services'))  # Or a relevant route

    return render_template('view_reviews.html', reviews=reviews, service_id=service_id)

