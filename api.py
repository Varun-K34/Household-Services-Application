from flask_restful import Resource, Api
from flask import request
from app import app
from models import db, Service, ServiceRequest, Review

api = Api(app)

# Endpoint to get all available services
class GetServices(Resource):
    def get(self):
        services = Service.query.all()
        return {
            'services': [{
                'id': service.id,
                'name': service.name,
                'description': service.description,
                'price': service.price
            } for service in services]
        }

# Endpoint to create a service request (Customer)
class CreateServiceRequest(Resource):
    def post(self):
        # Assuming data is sent in JSON format, e.g., { "service_id": 1, "customer_id": 1, "details": "Request details" }
        data = request.get_json()
        service_request = ServiceRequest(
            service_id=data['service_id'],
            customer_id=data['customer_id'],
            details=data['details'],
            status='pending'  # Initial status
        )
        db.session.add(service_request)
        db.session.commit()
        return {'message': 'Service request created successfully', 'id': service_request.id}, 201

# Endpoint to view service requests (Service Professional)
class ViewServiceRequests(Resource):
    def get(self):
        # This would be filtered by service professional or status as required
        requests = ServiceRequest.query.all()  # For simplicity, all requests
        return {
            'requests': [{
                'id': request.id,
                'service_name': request.service.name,
                'customer_name': request.customer.name,
                'status': request.status
            } for request in requests]
        }

# Endpoint for customers to submit a review for a service
class SubmitReview(Resource):
    def post(self):
        data = request.get_json()  # Expecting data like { "service_id": 1, "customer_id": 1, "rating": 5, "comments": "Great service!" }
        review = Review(
            service_id=data['service_id'],
            customer_id=data['customer_id'],
            rating=data['rating'],
            comments=data.get('comments', '')
        )
        db.session.add(review)
        db.session.commit()
        return {'message': 'Review submitted successfully', 'review_id': review.id}, 201

# Registering resources with API
api.add_resource(GetServices, '/api/services')
api.add_resource(CreateServiceRequest, '/api/service_request')
api.add_resource(ViewServiceRequests, '/api/service_requests')
api.add_resource(SubmitReview, '/api/reviews')
