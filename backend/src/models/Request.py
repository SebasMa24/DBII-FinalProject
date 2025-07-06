from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    phone: Optional[int] = None
    birthday: str
    region: str

class AddressCreate(BaseModel):
    user_id: int
    address: str
    city: str
    zipcode: int
    region: str

class OrderCreate(BaseModel):
    user_id: int
    coupon_id: Optional[int] = None
    total_price: int
    region: str

class OrderDetailCreate(BaseModel):
    order_id: int
    product_id: int
    quantity: int
    unit_price: int
    region: str