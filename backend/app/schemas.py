from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class RegisterIn(BaseModel):
    name:str; email:EmailStr; phone:Optional[str]=None; password:str=Field(min_length=8); role:str="consumer"
    latitude:Optional[float]=None; longitude:Optional[float]=None; address:Optional[str]=None
class LoginIn(BaseModel): email:EmailStr; password:str
class ProductIn(BaseModel):
    name:str; description:str=""; category:str; price:float=Field(gt=0); stock:int=Field(ge=0)
    latitude:Optional[float]=None; longitude:Optional[float]=None
class CartItemIn(BaseModel): product_id:int; quantity:int=Field(gt=0)
class OrderIn(BaseModel):
    items:list[CartItemIn]; delivery_address:str; delivery_latitude:Optional[float]=None; delivery_longitude:Optional[float]=None; payment_method:str="simulation"
class ReviewIn(BaseModel): rating:int=Field(ge=1,le=5); comment:str=""
class ComplaintIn(BaseModel): order_id:Optional[int]=None; against_user_id:Optional[int]=None; subject:str; description:str
class ComplaintUpdate(BaseModel): status:str; admin_note:Optional[str]=None
class ResetRequest(BaseModel): email:EmailStr
class ResetPasswordIn(BaseModel): token:str; new_password:str=Field(min_length=8)
