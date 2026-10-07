from fastapi import FastAPI, Depends, HTTPException,Request
from sqlalchemy.orm import Session
import stripe
from fastapi import WebSocket, WebSocketDisconnect
import uuid
from database import engine, get_db
from model import Base, User,Product,Cart,CartItem,Order,OrderItem,Payment,Notification
from schemas import UserRegister, UserResponse,UserLogin,TokenResponse,ProductCreate,ProductResponse,CartItemCreate,CartItemResponse,CartResponse,CartItemUpdate,CartItemDetail,OrderItemResponse,OrderResponse,PaymentCreate,PaymentResponse,NotificationCreate,NotificationResponse
from auth import hash_password,verify_password,create_access_token,get_current_user,get_admin_or_staff
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import os
from dotenv import load_dotenv

load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="E-Commerce API",
    version="1.0.0"
)
mail_config = ConnectionConfig(
    MAIL_USERNAME = os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD"),
    MAIL_FROM="veerankidivyasrisudharani@gmail.com",
    MAIL_PORT=465,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True
)
from typing import Dict
from fastapi import WebSocket

active_connections: Dict[int, WebSocket] = {}


@app.websocket("/ws/notifications/{user_id}")
async def websocket_notifications(
    websocket: WebSocket,
    user_id: int
):
    await websocket.accept()

    active_connections[user_id] = websocket

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        active_connections.pop(user_id, None)


async def send_realtime_notification(
    user_id: int,
    message: str
):
    websocket = active_connections.get(user_id)

    if websocket:
        await websocket.send_json({
            "user_id": user_id,
            "message": message
        })

@app.get("/")
def home():
    return {
        "message": "E-Commerce API is running",
        "database": "MySQL connected"
    }


@app.post("/register", response_model=UserResponse)
def register(
    user: UserRegister,
    db: Session = Depends(get_db)
):
    existing_user = (
        db.query(User)
        .filter(User.email == user.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    new_user = User(
        name=user.name,
        email=user.email,
        password=hash_password(user.password),
        role="customer"
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user
@app.post("/login", response_model=TokenResponse)
def login(
    user: UserLogin,
    db: Session = Depends(get_db)
):
    existing_user = (
        db.query(User)
        .filter(User.email == user.email)
        .first()
    )

    if not existing_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(
        user.password,
        existing_user.password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        {
            "sub": existing_user.email,
            "role": existing_user.role
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
@app.get("/profile")
def profile(
    current_user: dict = Depends(get_current_user)
):
    return {
        "message": "Profile accessed successfully",
        "user": current_user
    }
@app.post("/products", response_model=ProductResponse)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db)
):
    new_product = Product(
        name=product.name,
        description=product.description,
        price=product.price,
        stock=product.stock
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product
# @app.get("/products", response_model=list[ProductResponse])
# def get_products(
#     db: Session = Depends(get_db)
# ):
#     products = db.query(Product).all()
#     return products
@app.get("/products", response_model=list[ProductResponse])
def get_products(
    category: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    sort_by_popularity: bool = False,
    db: Session = Depends(get_db)
):
    query = db.query(Product)

    # Filter by category
    if category:
        query = query.filter(Product.category == category)

    # Filter by minimum price
    if min_price is not None:
        query = query.filter(Product.price >= min_price)

    # Filter by maximum price
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    # Sort by popularity
    if sort_by_popularity:
        query = query.order_by(Product.popularity.desc())

    return query.all()
@app.get("/products/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return product
@app.put("/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product: ProductCreate,
    db: Session = Depends(get_db)
):
    existing_product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if not existing_product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    existing_product.name = product.name
    existing_product.description = product.description
    existing_product.price = product.price
    existing_product.stock = product.stock

    db.commit()
    db.refresh(existing_product)

    return existing_product
@app.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    db.delete(product)
    db.commit()

    return {
        "message": "Product deleted successfully"
    }
@app.post("/cart/items", response_model=CartItemResponse)
def add_to_cart(
    item: CartItemCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # 1. Get the logged-in user's email
    user_email = (
        current_user["email"]
        if isinstance(current_user, dict)
        else current_user
    )

    # 2. Find the user
    user = (
        db.query(User)
        .filter(User.email == user_email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # 3. Find the product
    product = (
        db.query(Product)
        .filter(Product.id == item.product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # 4. Check stock
    if product.stock < item.quantity:
        raise HTTPException(
            status_code=400,
            detail="Not enough stock available"
        )

    # 5. Find the user's cart
    cart = (
        db.query(Cart)
        .filter(Cart.user_id == user.id)
        .first()
    )

    # 6. Create cart if it doesn't exist
    if not cart:
        cart = Cart(user_id=user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)

    # 7. Create cart item
    cart_item = CartItem(
        cart_id=cart.id,
        product_id=product.id,
        quantity=item.quantity
    )

    # 8. Save cart item
    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)

    # 9. Return cart item
    return cart_item
@app.get("/cart", response_model=CartResponse)
def get_cart(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user_email = (
        current_user["email"]
        if isinstance(current_user, dict)
        else current_user
    )

    user = db.query(User).filter(
        User.email == user_email
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    cart = db.query(Cart).filter(
        Cart.user_id == user.id
    ).first()

    if not cart:
        return CartResponse(
            cart_id=0,
            user_id=user.id,
            items=[]
        )

    cart_items = db.query(CartItem).filter(
        CartItem.cart_id == cart.id
    ).all()

    items = []

    for item in cart_items:
        product = db.query(Product).filter(
            Product.id == item.product_id
        ).first()

        if product:
            items.append(
                CartItemDetail(
                    product_id=product.id,
                    product_name=product.name,
                    price=product.price,
                    quantity=item.quantity
                )
            )

    return CartResponse(
        cart_id=cart.id,
        user_id=user.id,
        items=items
    )
@app.put("/cart/items/{cart_item_id}", response_model=CartItemResponse)
def update_cart_item(
    cart_item_id: int,
    item: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    user_email = (
        current_user["email"]
        if isinstance(current_user, dict)
        else current_user
    )

    user = (
        db.query(User)
        .filter(User.email == user_email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    cart = (
        db.query(Cart)
        .filter(Cart.user_id == user.id)
        .first()
    )

    if not cart:
        raise HTTPException(
            status_code=404,
            detail="Cart not found"
        )

    cart_item = (
        db.query(CartItem)
        .filter(
            CartItem.id == cart_item_id,
            CartItem.cart_id == cart.id
        )
        .first()
    )

    if not cart_item:
        raise HTTPException(
            status_code=404,
            detail="Cart item not found"
        )

    if item.quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be greater than 0"
        )

    cart_item.quantity = item.quantity

    db.commit()
    db.refresh(cart_item)

    return cart_item

@app.delete("/cart/items/{cart_item_id}")
def delete_cart_item(
    cart_item_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    user_email = (
        current_user["email"]
        if isinstance(current_user, dict)
        else current_user
    )

    user = (
        db.query(User)
        .filter(User.email == user_email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    cart = (
        db.query(Cart)
        .filter(Cart.user_id == user.id)
        .first()
    )

    if not cart:
        raise HTTPException(
            status_code=404,
            detail="Cart not found"
        )

    cart_item = (
        db.query(CartItem)
        .filter(
            CartItem.id == cart_item_id,
            CartItem.cart_id == cart.id
        )
        .first()
    )

    if not cart_item:
        raise HTTPException(
            status_code=404,
            detail="Cart item not found"
        )

    db.delete(cart_item)
    db.commit()

    return {
        "message": "Cart item deleted successfully"
    }
@app.post("/orders", response_model=OrderResponse)
async def create_order(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # Get logged-in user's email from JWT
    user_email = (
        current_user["email"]
        if isinstance(current_user, dict)
        else current_user
    )

    # Find user
    user = db.query(User).filter(
        User.email == user_email
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Find user's cart
    cart = db.query(Cart).filter(
        Cart.user_id == user.id
    ).first()

    if not cart:
        raise HTTPException(
            status_code=404,
            detail="Cart not found"
        )

    # Get cart items
    cart_items = db.query(CartItem).filter(
        CartItem.cart_id == cart.id
    ).all()

    if not cart_items:
        raise HTTPException(
            status_code=400,
            detail="Cart is empty"
        )

    # Calculate total
    total_amount = 0
    order_items_data = []

    for cart_item in cart_items:

        # Find product
        product = db.query(Product).filter(
            Product.id == cart_item.product_id
        ).first()

        if not product:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        # Check stock
        if product.stock < cart_item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough stock for {product.name}"
            )

        # Calculate item total
        item_total = product.price * cart_item.quantity
        total_amount += item_total

        order_items_data.append({
            "product": product,
            "quantity": cart_item.quantity,
            "price": product.price
        })

    # Create order
    order = Order(
        user_id=user.id,
        total_amount=total_amount,
        status="pending"
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    # Create order items
    response_items = []

    for item in order_items_data:

        product = item["product"]

        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=item["quantity"],
            price=item["price"]
        )

        db.add(order_item)

        # Reduce product stock
        product.stock -= item["quantity"]

        response_items.append(
            OrderItemResponse(
                product_id=product.id,
                quantity=item["quantity"],
                price=item["price"]
            )
        )

    # Clear cart
    for cart_item in cart_items:
        db.delete(cart_item)

    db.commit()

    # Create order notification
    notification = Notification(
        user_id=user.id,
        type="order",
        message=f"Your order #{order.id} has been placed successfully."
    )

    db.add(notification)
    db.commit()
    await send_realtime_notification(
    user.id,
    f"Your order #{order.id} has been placed successfully."
    )

    # Return order response
    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        total_amount=order.total_amount,
        status=order.status,
        items=response_items
    )
@app.get("/orders", response_model=list[OrderResponse])
def get_orders(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    user_email = (
        current_user["email"]
        if isinstance(current_user, dict)
        else current_user
    )

    # Find logged-in user
    user = (
        db.query(User)
        .filter(User.email == user_email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Get user's orders
    orders = (
        db.query(Order)
        .filter(Order.user_id == user.id)
        .order_by(Order.id.desc())
        .all()
    )

    result = []

    for order in orders:
        order_items = (
            db.query(OrderItem)
            .filter(OrderItem.order_id == order.id)
            .all()
        )

        items = []

        for item in order_items:
            items.append(
                OrderItemResponse(
                    product_id=item.product_id,
                    quantity=item.quantity,
                    price=item.price
                )
            )

        result.append(
            OrderResponse(
                id=order.id,
                user_id=order.user_id,
                total_amount=order.total_amount,
                status=order.status,
                items=items
            )
        )

    return result

@app.post("/payments", response_model=PaymentResponse)
def create_payment(
    payment: PaymentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Get logged-in user's email
    user_email = (
        current_user["email"]
        if isinstance(current_user, dict)
        else current_user
    )

    # Find user
    user = (
        db.query(User)
        .filter(User.email == user_email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Find user's order
    order = (
        db.query(Order)
        .filter(
            Order.id == payment.order_id,
            Order.user_id == user.id
        )
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    # Make sure order is pending
    if order.status != "pending":
        raise HTTPException(
            status_code=400,
            detail="Order is not pending"
        )

    # Create Stripe PaymentIntent
    payment_intent = stripe.PaymentIntent.create(
    amount=int(order.total_amount * 100),
    currency="inr",
    payment_method="pm_card_visa",
    confirm=True,
    automatic_payment_methods={
        "enabled": True,
        "allow_redirects": "never"
       },
    metadata={
        "order_id": str(order.id),
        "user_id": str(user.id)
      }
    )
    # Save payment in MySQL
    payment_status = "success" if payment_intent.status == "succeeded" else "pending"

    new_payment = Payment(
    order_id=order.id,
    amount=order.total_amount,
    payment_method="stripe",
    transaction_id=payment_intent.id,
    status=payment_status
    )

    if payment_status == "success":
        order.status = "paid"

        notification = Notification(
        user_id=user.id,
        type="payment",
        message=f"Payment for order #{order.id} was successful."
        )
        db.add(notification)

        db.add(new_payment)
        db.commit()
        db.refresh(new_payment)

        return new_payment

@app.post("/stripe/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    payload = await request.body()

    try:
        event = stripe.Event.construct_from(
            __import__("json").loads(payload),
            stripe.api_key
        )
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid Stripe event"
        )

    if event["type"] == "payment_intent.succeeded":

        payment_intent = event["data"]["object"]

        transaction_id = payment_intent["id"]

        payment = (
            db.query(Payment)
            .filter(
                Payment.transaction_id == transaction_id
            )
            .first()
        )

        if payment:
            payment.status = "success"

            order = (
                db.query(Order)
                .filter(Order.id == payment.order_id)
                .first()
            )

            if order:
                order.status = "paid"

            db.commit()

    elif event["type"] == "payment_intent.payment_failed":

        payment_intent = event["data"]["object"]

        transaction_id = payment_intent["id"]

        payment = (
            db.query(Payment)
            .filter(
                Payment.transaction_id == transaction_id
            )
            .first()
        )

        if payment:
            payment.status = "failed"

            order = (
                db.query(Order)
                .filter(Order.id == payment.order_id)
                .first()
            )

            if order:
                order.status = "failed"

            db.commit()

    return {"received": True}
@app.post("/stripe/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    ...

@app.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user_email = current_user["email"] if isinstance(current_user, dict) else current_user

    user = db.query(User).filter(User.email == user_email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == user.id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order_items = db.query(OrderItem).filter(
        OrderItem.order_id == order.id
    ).all()

    items = []

    for item in order_items:
        items.append(
            OrderItemResponse(
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.price
            )
        )

    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        total_amount=order.total_amount,
        status=order.status,
        items=items
    )
@app.get("/payments/{order_id}", response_model=PaymentResponse)
def get_payment(
    order_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user_email = current_user["email"] if isinstance(current_user, dict) else current_user

    user = db.query(User).filter(User.email == user_email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == user.id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    payment = db.query(Payment).filter(
        Payment.order_id == order.id
    ).first()

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    return payment
@app.post("/notifications", response_model=NotificationResponse)
def create_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user_email = current_user["email"] if isinstance(current_user, dict) else current_user

    user = db.query(User).filter(User.email == user_email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_notification = Notification(
        user_id=user.id,
        type=notification.type,
        message=notification.message,
        is_read=False
    )

    db.add(new_notification)
    db.commit()
    db.refresh(new_notification)

    return new_notification
@app.get("/notifications", response_model=list[NotificationResponse])
def get_notifications(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user_email = current_user["email"] if isinstance(current_user, dict) else current_user

    user = db.query(User).filter(User.email == user_email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == user.id)
        .order_by(Notification.id.desc())
        .all()
    )

    return notifications
@app.put("/notifications/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user_email = current_user["email"] if isinstance(current_user, dict) else current_user

    user = db.query(User).filter(User.email == user_email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user.id
    ).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True

    db.commit()
    db.refresh(notification)

    return notification

@app.put("/orders/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    new_status: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_admin_or_staff)
):
    # Get logged-in user
    user_email = (
        current_user["email"]
        if isinstance(current_user, dict)
        else current_user
    )

    user = db.query(User).filter(
        User.email == user_email
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Find order
    order = db.query(Order).filter(
        Order.id == order_id
    ).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    # Allowed statuses
    allowed_statuses = [
        "pending",
        "paid",
        "confirmed",
        "shipped",
        "delivered",
        "cancelled",
        "failed"
    ]

    if new_status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid order status"
        )

    # Update status
    order.status = new_status

    # Create notification
    notification_type = "shipping" if new_status == "shipped" else "order"

    notification = Notification(
        user_id=order.user_id,
        type=notification_type,
        message=f"Your order #{order.id} status is now {new_status}."
    )

    db.add(notification)
    db.commit()
    db.refresh(order)

    # Get order items
    order_items = db.query(OrderItem).filter(
        OrderItem.order_id == order.id
    ).all()

    response_items = []

    for item in order_items:
        response_items.append(
            OrderItemResponse(
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.price
            )
        )

    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        total_amount=order.total_amount,
        status=order.status,
        items=response_items
    )
@app.post("/products", response_model=ProductResponse)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_admin_or_staff)
):
    new_product = Product(
        name=product.name,
        description=product.description,
        price=product.price,
        stock=product.stock
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product
@app.put("/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_admin_or_staff)
):
    existing_product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not existing_product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    existing_product.name = product.name
    existing_product.description = product.description
    existing_product.price = product.price
    existing_product.stock = product.stock

    db.commit()
    db.refresh(existing_product)

    return existing_product
@app.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_admin_or_staff)
):
    existing_product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not existing_product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    db.delete(existing_product)
    db.commit()

    return {
        "message": "Product deleted successfully"
    }
@app.post("/products", response_model=ProductResponse)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_admin_or_staff)
):
    new_product = Product(
        name=product.name,
        description=product.description,
        price=product.price,
        stock=product.stock,
        category=product.category,
        popularity=product.popularity
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product
@app.post("/products", response_model=ProductResponse)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_admin_or_staff)
):
    new_product = Product(
        name=product.name,
        description=product.description,
        price=product.price,
        stock=product.stock,
        category=product.category,
        popularity=product.popularity
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product
@app.put("/cart/items/{item_id}")
def update_cart_item(
    item_id: int,
    item: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user_email = current_user["email"] if isinstance(current_user, dict) else current_user

    user = db.query(User).filter(User.email == user_email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    cart = db.query(Cart).filter(Cart.user_id == user.id).first()

    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    cart_item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.cart_id == cart.id
    ).first()

    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    product = db.query(Product).filter(
        Product.id == cart_item.product_id
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if item.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than 0")

    if product.stock < item.quantity:
        raise HTTPException(status_code=400, detail="Not enough stock")

    cart_item.quantity = item.quantity

    db.commit()
    db.refresh(cart_item)

    return cart_item
@app.delete("/cart/items/{item_id}")
def remove_cart_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user_email = current_user["email"] if isinstance(current_user, dict) else current_user

    user = db.query(User).filter(User.email == user_email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    cart = db.query(Cart).filter(Cart.user_id == user.id).first()

    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    cart_item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.cart_id == cart.id
    ).first()

    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    db.delete(cart_item)
    db.commit()

    return {"message": "Cart item removed successfully"} 
@app.post("/test-email")
async def test_email():
    message = MessageSchema(
        subject="E-Commerce Test Email",
        recipients=["YOUR_EMAIL@gmail.com"],
        body="Email notification is working successfully.",
        subtype="plain"
    )

    fm = FastMail(mail_config)
    await fm.send_message(message)

    return {"message": "Test email sent successfully"}
