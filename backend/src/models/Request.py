from pydantic import BaseModel
from typing import Optional

"""
Input Models for E-commerce API (Create Operations)

These Pydantic models define the expected structure of data for create (POST) operations 
in the e-commerce platform. Each model represents the data required to insert new records 
into the corresponding database tables.

Note:
Due to time constraints, these input models were kept minimal and may lack validations, 
constraints, or nested relationships that would be recommended in a full-scale production system.

Shared Characteristics:
- `region` is used consistently for multi-region support.
- All fields are required unless explicitly marked as Optional.
- Types are loosely defined (e.g., `birthday` as str instead of `datetime`) for simplicity 
  and flexibility during initial development.

Models Overview:
----------------

- `UserCreate`: Basic registration model with name, email, password, phone, birthday, and region.
- `AddressCreate`: Address data for a specific user including city, zipcode, and region.
- `OrderCreate`: Used to create a new order with optional coupon.
- `OrderDetailCreate`: Defines the structure for individual items in an order (product, quantity, price).

Recommendation:
As the system evolves, it is recommended to:
- Add stricter validation (e.g., date formats, min/max values).
- Use `datetime` for date fields like `birthday`.
- Add custom validators for complex logic (e.g., region restrictions).
"""

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