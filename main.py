from typing import Annotated, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Response, status
from pydantic import BaseModel
from pydantic.functional_validators import AfterValidator
from db_client import Budget_db


app = FastAPI()


def get_db():
    return Budget_db()


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


@app.get("/budgets")
def main(db: Budget_db = Depends(get_db)):
    try:
        budgets = db.select_all()
        return budgets
    except Exception as e:
        print(f"Selectall Error : {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.post("/budgets", status_code=status.HTTP_201_CREATED)
def insert(
    item: item,
    db: Budget_db = Depends(get_db),
):
    try:
        db.insert(
            item.date, item.credit_or_debit, item.amount, item.category, item.comments
        )
        return {"added data": item}
    except Exception as e:
        print(f"Insert Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.get("/budgets/{id}")
def get_by_id(id: int, db: Budget_db = Depends(get_db)):
    try:
        budget = db.get_by_id(id)
        if not budget:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"record id : {id} not found",
            )
        return budget
    except Exception as e:
        print(f"get_by_id: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.delete("/budgets/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    id: int,
    db: Budget_db = Depends(get_db),
):
    try:
        db.delete(id)
        return {"delete": id}
    except Exception as e:
        print(f"Delete Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
