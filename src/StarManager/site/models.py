from typing import List, Optional, Union

from pydantic import AliasPath, BaseModel, Field, HttpUrl


class UserPremium(BaseModel):
    duration: int
    gift: bool = False
    gift_link: Optional[str] = None
    promo: Optional[str] = None
    payment: str


class ChatPremium(BaseModel):
    chat_id: Optional[int] = Field(None, ge=1, le=2147483647)
    promo: Optional[str] = None
    payment: str


class Coins(BaseModel):
    value: int
    payment: str


class Item(BaseModel):
    type: str
    data: Union[UserPremium, ChatPremium, Coins]


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


class Payment(BaseModel):
    yookassa_order_id: str = Field(..., alias="id")
    order_id: int = Field(..., validation_alias=AliasPath("metadata", "pid"))
    cost: int = Field(..., validation_alias=AliasPath("metadata", "origcost"))
    final_cost: str = Field(..., validation_alias=AliasPath("amount", "value"))
    chat_id: Optional[int] = Field(None, validation_alias=AliasPath("metadata", "chat_id"))
    coins: Optional[int] = Field(None, validation_alias=AliasPath("metadata", "coins"))
    from_id: int = Field(..., alias="merchant_customer_id")
    to_id: Optional[int] = Field(None, validation_alias=AliasPath("metadata", "gift"))
    personal_promo: Optional[int] = Field(None, validation_alias=AliasPath("metadata", "personal"))
    delete_cmid: Optional[int] = Field(None, validation_alias=AliasPath("metadata", "del_cmid"))

    def model_post_init(self, _):
        if not self.to_id:
            self.to_id = self.from_id


class LeaderboardItem(BaseModel):
    place: int
    avatar: HttpUrl
    domain: str
    username: str
    value: str


class LeaderboardPage(BaseModel):
    total: int
    items: List[LeaderboardItem]
