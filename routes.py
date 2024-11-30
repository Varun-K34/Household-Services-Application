import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from app import app
from models import db, User, Service, ServiceRequest, ServiceProfessional, Customer, Review
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime

# Set your upload folder path in the configuration
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'resumes')  # Example directory for uploads

# ----------------------------------------------
# Authentication Endpoints (4)
# ----------------------------------------------

@app.route("/")
def home():
    return render_template("login.html")

@app.route('/register/customer', methods=["GET", "POST"])
def register_customer():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        email = request.form.get('email')
        phone_number = request.form.get('phone_number')  # Get the phone number
        address = request.form.get('address')
        pin_code = request.form.get('pin_code')

        # Check if required fields are filled
        if not username or not password or not confirm_password or not email or not phone_number:
            flash('Please fill out all fields')
            return redirect(url_for('register_customer'))
        
        # Password match validation
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('register_customer'))

        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register_customer'))
        
        # Check if phone number already exists
        existing_user = User.query.filter_by(phone_number=phone_number).first()
        if existing_user:
            flash('Phone number is already registered!', 'danger')
            return redirect(url_for('register_customer'))  # Redirect to the registration page with a message

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Create new user
        new_user = User(username=username, password_hash=hashed_password, email=email, phone_number=phone_number, role='customer')
        db.session.add(new_user)
        db.session.commit()  # Commit to generate the user ID

        # Now create the customer, linking the user via the user_id foreign key
        new_customer = Customer(user_id=new_user.id, address=address, pin_code=pin_code)
        db.session.add(new_customer)
        db.session.commit()  # Commit the customer record

        flash('Customer registration successful')
        return redirect(url_for('login'))

    return render_template('customer/register_customer.html')


@app.route('/register/professional', methods=["GET", "POST"])
def register_professional():
    if request.method == "POST":
        # Fetch form data
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        email = request.form.get('email')
        phone_number = request.form.get('phone_number')  # Get the phone number
        service_type = request.form.get('service_type')
        experience = request.form.get('experience')
        address = request.form.get('address')
        pin_code = request.form.get('pin_code')
        description = request.form.get('description')

        # Handling file uploads for resume
        document = request.files.get('document')  # Get the document from the form
        document_filename = None

        # Check if a document was uploaded
        if document:
            # Secure the filename and save the document
            filename = secure_filename(document.filename)
            document_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            document.save(document_path)  # Save the document

            document_filename = filename  # Store the filename to save in the database later

        # Validate required fields
        if not username or not password or not confirm_password or not email or not phone_number or not service_type or not experience:
            flash('Please fill out all required fields')
            return redirect(url_for('register_professional'))
        
        # Check password match
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('register_professional'))

        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register_professional'))
        
        # Check if phone number already exists
        existing_user = User.query.filter_by(phone_number=phone_number).first()
        if existing_user:
            flash('Phone number is already registered!', 'danger')
            return redirect(url_for('register_professional'))  # Redirect to the registration page with a message

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Create new user with phone number
        new_user = User(username=username, password_hash=hashed_password, email=email, phone_number=phone_number, role='professional')
        db.session.add(new_user)
        db.session.commit()  # Commit to generate the user ID

        # Check if the service_type exists in the Service model
        service = Service.query.filter_by(name=service_type).first()
        if not service:
            flash(f"Service '{service_type}' not found. Please select a valid service.")
            return redirect(url_for('register_professional'))
        
        # Now create the service professional, linking the user via the user_id foreign key
        new_professional = ServiceProfessional(
            user_id=new_user.id, 
            service_type=service_type,
            experience=experience, 
            address=address, 
            pin_code=pin_code,
            description=description,
            resume_filename=document_filename,  # Save the resume file path
            service_id=service.id  # Set the service_id to the matching service's id
        )
        db.session.add(new_professional)
        db.session.commit()  # Commit the service professional record

        flash('Service Professional registration successful')
        return redirect(url_for('login'))

    return render_template('professional/register_professional.html')



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
        # flash('Login successful')
        
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

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'role' not in session or session['role'] != 'admin':
        flash('Unauthorized access. You must be logged in as an admin to view this page.', 'danger')
        return redirect(url_for('login'))

    # Fetch data related to users and services
    users = User.query.all()
    services = Service.query.all()
    professionals = ServiceProfessional.query.all()
    service_requests = ServiceRequest.query.all()

    return render_template('admin/dashboard.html', users=users, services=services, professionals=professionals, service_requests=service_requests)


@app.route('/admin/approve_professional/<int:professional_id>', methods=["POST"])
def approve_professional(professional_id):
    if 'role' not in session or session['role'] != 'admin':
        flash('Unauthorized access')
        return redirect(url_for('login'))

    professional = ServiceProfessional.query.get(professional_id)
    if not professional:
        flash('Invalid professional')
        return redirect(url_for('admin_dashboard'))

    professional.is_approved = True
    db.session.commit()
    flash('Professional approved')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject_professional/<int:professional_id>', methods=["POST"])
def reject_professional(professional_id):
    if 'role' not in session or session['role'] != 'admin':
        flash('Unauthorized access')
        return redirect(url_for('login'))

    professional = ServiceProfessional.query.get(professional_id)
    if not professional:
        flash('Invalid professional')
        return redirect(url_for('admin_dashboard'))

    # Set the professional's approval status to False or delete if needed
    professional.is_approved = False
    db.session.commit()

    flash('Professional rejected')
    return redirect(url_for('admin_dashboard'))



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

@app.route('/view_professional/<int:professional_id>')
def view_professional(professional_id):
    # Fetch the professional from the database using the professional_id
    professional = ServiceProfessional.query.get_or_404(professional_id)
    
    # Pass the professional to the template to display their details
    return render_template('admin/view_professional.html', professional=professional)


@app.route('/service/add', methods=["GET", "POST"])
def add_service():
    if request.method == "POST":
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')

        # Validation for missing fields
        if not name or not description or not price:
            flash('Please fill out all fields')
            return redirect(url_for('add_service'))

        # Validation for price (ensure it's a positive number)
        try:
            price = float(price)
            if price <= 0:
                flash('Price must be a positive number')
                return redirect(url_for('add_service'))
        except ValueError:
            flash('Price must be a valid number')
            return redirect(url_for('add_service'))

        # Add the service to the database
        service = Service(name=name, description=description, price=price)
        db.session.add(service)
        db.session.commit()
        flash('Service added successfully')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin/add_service.html')


@app.route('/service/<int:service_id>/edit', methods=["GET", "POST"])
def edit_service(service_id):
    service = Service.query.get(service_id)
    if not service:
        flash('Service not found', 'error')
        return redirect(url_for('admin_dashboard'))

    if request.method == "POST":
        # Update the service details
        service.name = request.form.get('name')
        service.description = request.form.get('description')
        service.price = request.form.get('price')  # Update the base price
        
        # Commit changes to the database
        db.session.commit()

        flash('Service updated successfully', 'success')
        return redirect(url_for('admin_dashboard'))

    # Render the edit service page with the current service details
    return render_template('admin/edit_service.html', service=service)

@app.route('/view_service/<int:service_id>')
def view_service(service_id):
    # Fetch the service from the database using the service_id
    service = Service.query.get_or_404(service_id)
    
    # Pass the service to the template to display its details
    return render_template('admin/view_service.html', service=service)



@app.route('/service/<int:service_id>/delete', methods=["POST"])
def delete_service(service_id):
    service = Service.query.get(service_id)
    
    if service:
        # Check if there are any associated ServiceProfessional entries
        associated_professionals = ServiceProfessional.query.filter_by(service_id=service_id).all()
        
        if associated_professionals:
            # If there are associated professionals, show a flash message
            flash('Service cannot be deleted because there are professionals associated with it. Please remove professionals first.', 'danger')
        else:
            # If no professionals are associated, delete the service
            db.session.delete(service)
            db.session.commit()
            flash('Service deleted successfully', 'success')
    else:
        flash('Service not found', 'danger')

    return redirect(url_for('admin_dashboard'))




@app.route('/view_request/<int:request_id>')
def view_request(request_id):
    # Fetch the service request from the database using the request_id
    request = ServiceRequest.query.get_or_404(request_id)
    
    # Pass the request to the template
    return render_template('admin/view_request.html', request=request)

@app.route('/close_request/<int:request_id>', methods=['POST'])
def close_request(request_id):
    # Fetch the service request from the database
    service_request = ServiceRequest.query.get_or_404(request_id)

    # Update the status to 'closed' if it's not already
    if service_request.status != 'closed':
        service_request.status = 'closed'
        db.session.commit()
        flash('Service request has been closed successfully.', 'success')
    else:
        flash('Service request is already closed.', 'info')

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/search', methods=['GET', 'POST'])
def admin_search():
    search_results = []
    search_text = ''
    search_type = None
    
    if request.method == 'POST':
        search_text = request.form.get('search_text', '').strip()
        search_type = request.form.get('search_type')

        if search_type == 'services' and search_text:
            search_results = Service.query.filter(Service.name.ilike(f'%{search_text}%')).all()

        elif search_type == 'professionals' and search_text:
            # Search on multiple fields in ServiceProfessional and User models
            search_results = ServiceProfessional.query.join(User).filter(
                (User.username.ilike(f'%{search_text}%')) |  # Search by username
                (ServiceProfessional.id.ilike(f'%{search_text}%')) |  # Search by professional ID
                (ServiceProfessional.service_type.ilike(f'%{search_text}%')) |  # Search by service type
                (ServiceProfessional.experience.ilike(f'%{search_text}%')) |  # Search by experience
                (ServiceProfessional.address.ilike(f'%{search_text}%'))  # Search by address
            ).all()

        elif search_type == 'service_requests' and search_text:
            search_results = ServiceRequest.query.filter(ServiceRequest.id.ilike(f'%{search_text}%')).all()

    return render_template('admin/search.html', 
                           search_results=search_results, 
                           search_type=search_type, 
                           search_text=search_text)








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
    # Ensure user is logged in as a professional
    if 'role' not in session or session['role'] != 'professional':
        flash('Unauthorized access. You must be logged in as a professional to view this page.', 'danger')
        return redirect(url_for('login'))

    # Fetch the logged-in professional's ID from session
    professional_id = session.get('user_id')

    # Fetch Today's Services (Pending Requests for the logged-in professional)
    today_requests = ServiceRequest.query.filter_by(
        professional_id=professional_id,
        status='requested'
    ).order_by(ServiceRequest.date_of_request).all()

    # Fetch Closed Services (Completed Requests for the logged-in professional)
    closed_requests = ServiceRequest.query.filter_by(
        professional_id=professional_id,
        status='closed'
    ).order_by(ServiceRequest.date_of_completion.desc()).all()

    # Transform closed_requests into a list of dictionaries for easy rendering
    closed_requests_list = []
    for service, review in closed_requests:
        closed_requests_list.append({
            'id': service.id,
            'customer_name': service.customer_ref.user_ref.username,
            'customer_contact': service.customer_ref.user_ref.phone_number,
            'customer_address': service.customer_ref.address,
            'customer_pincode': service.customer_ref.pincode,
            'service_request_date': service.date_of_request,
            'rating': review.rating,
            'remarks': review.remarks
        })

    # Render the dashboard template with fetched data
    return render_template(
        'professional/dashboard.html',
        today_requests=today_requests,
        closed_requests=closed_requests_list
    )

@app.route('/professional_profile', methods=['GET', 'POST'])
def professional_profile():
    # Authorization check
    if 'role' not in session or session['role'] != 'professional':
        flash('Unauthorized access. You must be logged in as a professional to view this page.', 'danger')
        return redirect(url_for('login'))

    # Fetch the professional's details
    professional = ServiceProfessional.query.filter_by(user_id=session['user_id']).first()

    if request.method == 'POST':
        # Update profile data
        professional.service_type = request.form.get('service_type')
        professional.experience = request.form.get('experience')
        professional.address = request.form.get('address')
        professional.pin_code = request.form.get('pin_code')
        professional.description = request.form.get('description')

        # Handle resume file upload
        resume_file = request.files.get('resume')
        if resume_file:
            filename = secure_filename(resume_file.filename)
            resume_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            resume_file.save(resume_path)
            professional.resume_filename = filename

        # Save changes
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('professional_profile'))

    return render_template('professional/profile.html', professional=professional)


@app.route('/professional/search', methods=['GET', 'POST'])
def professional_search():
    search_results = []
    search_text = ''
    search_type = None

    if request.method == 'POST':
        search_text = request.form.get('search_text', '').strip()
        search_type = request.form.get('search_type')

        # Search by ServiceRequest id for today services
        if search_type == 'today_services' and search_text:
            search_results = ServiceRequest.query.filter(
                ServiceRequest.id == search_text  # Searching by the ServiceRequest ID directly
            ).all()

        # You can add additional filters for closed services or other types of searches
        elif search_type == 'closed_services' and search_text:
            search_results = ServiceRequest.query.filter(
                ServiceRequest.id == search_text  # Searching by the ServiceRequest ID directly
            ).all()

    return render_template('professional/search.html', 
                           search_results=search_results, 
                           search_type=search_type, 
                           search_text=search_text)



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

