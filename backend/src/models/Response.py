from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from datetime import date


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