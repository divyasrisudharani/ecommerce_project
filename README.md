# E-Commerce Platform Backend

A full-featured E-Commerce backend developed using Django, Django REST Framework, FastAPI, and MySQL.

## Tech Stack

- Python
- Django
- Django REST Framework
- FastAPI
- MySQL
- SQLAlchemy
- JWT Authentication
- Stripe Test Mode
- WebSocket
- SMTP Email
- Postman
- Swagger / OpenAPI

## Project Structure

```text
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
## Key Features

- User registration and JWT-based authentication
- Secure password hashing
- Role-based access control for Customer, Staff, and Admin
- Product and category management
- Product image upload
- Product stock management
- Shopping cart management
- Cart item management
- Order creation and order history
- Order status management
- Stripe test-mode payment processing
- Stripe webhook handling
- Payment status tracking
- Database notifications
- Mark notifications as read
- Real-time WebSocket notifications
- Email notification support
- Django Admin management
- Order analytics dashboard
- Daily payment summary
- CSV report generation
- PDF report generation
- REST API development
- FastAPI Swagger/OpenAPI documentation
- Postman API testing
- MySQL database integration
- Environment-based configuration for sensitive credentials
- Git/GitHub version control
## Backend Architecture

The project uses two backend frameworks:

### Django Backend
Handles:
- User management
- Product management
- Orders
- Payments
- Notifications
- Admin dashboard
- Reports

### FastAPI Backend
Handles:
- FastAPI APIs
- JWT authentication
- Cart operations
- Order operations
- Payment processing
- Stripe integration
- WebSocket notifications
- API documentation