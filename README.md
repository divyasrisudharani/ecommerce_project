# E-Commerce Platform Backend

## Project Overview
Brief description of the e-commerce backend.

## Features
- User registration and JWT authentication
- Role-based access control
- Product and category management
- Cart management
- Order management
- Payment processing
- Stripe test integration and webhook
- Email notifications
- Real-time WebSocket notifications
- Django Admin dashboard
- Analytics
- CSV/PDF reports
- REST APIs
- Automated testing

## Technology Stack
- Python
- Django
- Django REST Framework
- FastAPI
- MySQL
- SQLAlchemy
- JWT
- Stripe
- WebSocket
- Pytest

## Project Structure
ecommerce_project/
├── django_backend/
│   ├── config/
│   ├── users/
│   ├── products/
│   ├── orders/
│   ├── payments/
│   └── notifications/
├── fastapi_backend/
│   ├── main.py
│   ├── database.py
│   ├── model.py
│   ├── schemas.py
│   └── auth.py
├── .gitignore
└── README.md

## API
Django API: http://127.0.0.1:8000/
FastAPI API: http://127.0.0.1:8001/
FastAPI Swagger: http://127.0.0.1:8001/docs

## Authentication
JWT-based authentication and role-based authorization.

## Security
- Environment variables for sensitive configuration
- Password hashing
- JWT authentication
- No credentials committed to GitHub
- .env excluded using .gitignore

## Testing

Django:
python manage.py test

FastAPI:
python -m pytest -q

## Screenshots
Screenshots of Admin, Swagger, Analytics, WebSocket, etc.

## How to Run

### Django
cd django_backend
python manage.py runserver

### FastAPI
cd fastapi_backend
uvicorn main:app --reload --port 8001

## Author
Divyasri sudharani

