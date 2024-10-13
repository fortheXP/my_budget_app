from datetime import datetime
from pydantic import BaseModel
from pydantic.functional_validators import AfterValidator
from typing import Annotated, Optional

def validate_date(value: str) -> str:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except Exception as e:
        raise e
    return value


yyyymmdd = Annotated[str, AfterValidator(validate_date)]


class item(BaseModel):
    date: yyyymmdd
    credit_or_debit: str
    amount: float
    category: str
    comments: Optional[str] = None


class ItemBase(BaseModel):
    date: yyyymmdd
    credit_or_debit: str
    amount: float
    category: str
    comments: Optional[str] = None


class UserCreate(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str

    class config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


class Token_Data(BaseModel):
    id: Optional[int] = None
