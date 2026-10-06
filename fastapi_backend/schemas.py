from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str

    class Config:
        from_attributes = True
        
class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str




# class ProductCreate(BaseModel):
#     name: str
#     description: str | None = None
#     price: float
#     stock: int
class ProductCreate(BaseModel):
    name: str
    description: str | None = None
    price: float
    stock: int
    category: str | None = None
    popularity: int = 0


# class ProductResponse(BaseModel):
#     id: int
#     name: str
#     description: str | None = None
#     price: float
#     stock: int

#     class Config:
#         from_attributes = True
class ProductResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    price: float
    stock: int
    category: str | None = None
    popularity: int

    class Config:
        from_attributes = True
class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = 1


class CartItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int

    class Config:
        from_attributes = True


class CartItemUpdate(BaseModel):
    quantity: int


class CartItemDetail(BaseModel):
    product_id: int
    product_name: str
    price: float
    quantity: int


class CartResponse(BaseModel):
    cart_id: int
    user_id: int
    items: list[CartItemDetail]
class OrderItemResponse(BaseModel):
    product_id: int
    quantity: int
    price: float


class OrderResponse(BaseModel):
    id: int
    user_id: int
    total_amount: float
    status: str
    items: list[OrderItemResponse]
class PaymentCreate(BaseModel):
    order_id: int
class PaymentResponse(BaseModel):
    id: int
    order_id: int
    amount: float
    payment_method: str
    transaction_id: str | None = None
    status: str

    class Config:
        from_attributes = True
class NotificationCreate(BaseModel):
    type: str = "general"
    message: str


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    type: str
    message: str
    is_read: bool

    class Config:
        from_attributes = True