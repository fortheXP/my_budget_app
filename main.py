from typing import Annotated, Optional
from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel
from pydantic.functional_validators import AfterValidator
from db_client import Budget_db


app = FastAPI()


budgetdb = Budget_db()


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


@app.get("/")
def root():
    return {"Happy": "Budgeting"}


@app.get("/selectall")
def main():
    return budgetdb.select_all()


@app.post("/insert")
def insert(item: item):
    budgetdb.insert(
        item.date, item.credit_or_debit, item.amount, item.category, item.comments
    )
    return {"added data": item}
