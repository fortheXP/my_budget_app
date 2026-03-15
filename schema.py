from datetime import datetime
from pydantic import BaseModel
from pydantic.functional_validators import AfterValidator
from typing import Annotated, Optional
from datetime import date


def validate_date(value: date) -> date:
    if value > date.today():
        raise ValueError("Date cannot be in the future")
    return value


yyyymmdd = Annotated[date, AfterValidator(validate_date)]

class UserCreate(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str

    class config:
        orm_mode = True


class item(BaseModel):
    date: yyyymmdd
    credit_or_debit: str
    amount: float
    category_id: int
    comments: Optional[str] = None

class BaseTransactions(BaseModel):
    date: date
    type: str 
    amount: float
    category_id: int
    user_id : int
    comment: Optional[str] = None

class CreateTransaction(BaseTransactions):
    pass

class Transactions(BaseTransactions):
    id : int 
    user_id : int
    user : UserOut

    class config:
        orm_mode = True

class ItemBase(BaseModel):
    date: yyyymmdd
    credit_or_debit: str
    amount: float
    category: str
    comments: Optional[str] = None




class Token(BaseModel):
    access_token: str
    token_type: str


class Token_Data(BaseModel):
    id: Optional[int] = None
