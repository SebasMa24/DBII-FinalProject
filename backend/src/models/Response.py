from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from datetime import date

"""
Response Models for E-commerce API

These Pydantic models define the structure of the API responses returned by various 
endpoints in the e-commerce system. Each model corresponds to a specific entity such 
as user, address, product, store, order, shipment, payment, etc.

Note:
Due to time constraints during development, most of these models were used in a limited 
manner—primarily for response serialization. Some nested fields were simplified and 
may not reflect the full depth of relationships or validation logic.

Shared Characteristics:
- All timestamps are returned in ISO 8601 format.
- All entities include a `region` field for partitioned multi-region support.
- Nested models (e.g., ProductResponse) include simplified submodels such as 
  CategoryResponse and StoreResponse.

Models Overview:
----------------

- `UserResponse`: Basic user info (id, name, email, region, created_at).
- `AddressResponse`: User address with location details.
- `StoreResponse`: Seller store info (simplified).
- `ProductResponse`: Product details including category, store, images, discounts, reviews.
- `CategoryResponse`: Product category metadata.
- `ImageResponse`: Product image metadata.
- `DiscountResponse`: Active discount applied to a product.
- `ReviewStatsResponse`: Aggregated review data (average, count).
- `QuestionResponse` and `AnswerResponse`: Q&A system models.
- `OrderResponse` and `OrderDetailResponse`: Order and itemized order detail.
- `ShipmentResponse`: Shipment tracking info.
- `PaymentResponse`: Payment metadata and status.
- `SearchHistoryResponse`: User search history (for analytics).
- `CampaignResponse` and `AdResponse`: Advertising and campaign data.
- `ProductBase`: Base structure used for product-related models.

Recommendation:
These models can be further extended for input validation, ORM integration, or 
OpenAPI documentation. For a production system, consider modularizing models 
(by domain) and enforcing stricter typing/validation rules.
"""

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    region: str
    created_at: datetime

class AddressResponse(BaseModel):
    id: int
    user_id: int
    address: str
    city: str
    zipcode: int
    region: str

class StoreResponse(BaseModel):
    id: int
    user_id: int
    name: str
    is_official: bool
    created_at: datetime
    region: str

class ImageResponse(BaseModel):
    id: Optional[int]
    url: str


class DiscountResponse(BaseModel):
    percentage: int
    start_date: datetime
    end_date: datetime
    isActive: bool


class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None


class StoreResponse(BaseModel):
    id: int
    name: str
    is_official: bool


class ReviewStatsResponse(BaseModel):
    average_rating: float
    total_reviews: int


class ProductResponse(BaseModel):
    id: int
    title: str
    user_id: int
    is_official: bool
    created_at: datetime
    region: str
    price: int
    discounted_price: Optional[int] = None
    stock: int
    description: Optional[str] = None
    category: CategoryResponse
    store: StoreResponse
    images: List[ImageResponse] = []
    active_discounts: List[DiscountResponse] = []
    review_stats: Optional[ReviewStatsResponse] = None

class QuestionResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    question_text: str
    created_at: datetime
    region: str

class AnswerResponse(BaseModel):
    id: int
    store_id: int
    question_id: int
    answer_text: str
    created_at: datetime
    region: str

class OrderResponse(BaseModel):
    id: int
    user_id: int
    coupon_id: Optional[int]
    total_price: int
    created_at: datetime
    region: str

class OrderDetailResponse(BaseModel):
    id: int
    order_id: int
    product_id: int
    quantity: int
    unit_price: int
    region: str

class ShipmentResponse(BaseModel):
    id: int
    order_id: int
    shipment_status_id: int
    tracking_number: Optional[int]
    carrier: Optional[str]
    shipped_at: Optional[datetime]
    delivered_at: Optional[datetime]
    region: str

class PaymentResponse(BaseModel):
    id: int
    order_id: int
    payment_method_id: int
    payment_status_id: int
    amount: int
    created_at: datetime
    region: str

class SearchHistoryResponse(BaseModel):
    id: int
    user_id: int
    search_query: str
    date: datetime
    region: str

class CampaignResponse(BaseModel):
    id: int
    store_id: int
    name: str
    start_date: date
    end_date: date
    status: str
    target_keywords: str
    region: str

class AdResponse(BaseModel):
    id: int
    campaign_id: int
    product_id: int
    image_url: str
    bid_amount: int
    click_amount: int
    region: str

class ProductBase(BaseModel):
    id: int
    title: str
    description: str
    price: int
    stock: int
    region: str
    created_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class CategoryResponse(BaseModel):
    id: int
    name: str
    description: str

class StoreResponse(BaseModel):
    id: int
    name: str
    is_official: bool

class ImageResponse(BaseModel):
    id: int
    url: str

class DiscountResponse(BaseModel):
    id: int
    percentage: int
    start_date: date
    end_date: date
    is_active: bool

class ReviewStats(BaseModel):
    average_rating: float
    total_reviews: int

class ProductResponse(ProductBase):
    category: CategoryResponse
    store: StoreResponse
    images: List[ImageResponse]
    active_discounts: List[DiscountResponse]
    review_stats: ReviewStats