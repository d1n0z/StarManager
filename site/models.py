from typing import Optional

from pydantic import BaseModel, Field


class Subscription(BaseModel):
    type: str
    duration: Optional[int] = None
    gift: Optional[bool] = False
    gift_link: Optional[str] = None
    promo: Optional[str] = None
    payment: str
    chat_id: Optional[int] = Field(None, ge=1, le=2147483647)



class User(BaseModel):
    id: int
    first_name: str
    last_name: str
    photo: Optional[str] = None
    email: Optional[str] = None


class PromoCheck(BaseModel):
    promo: str


class PaymentHistory(BaseModel):
    type: str
    date: str
    sum: int
    comment: str
