from sqlalchemy import func, and_
import schema
from fastapi import Depends, status, APIRouter, HTTPException
from app import oauth2
from sqlalchemy.orm import Session, joinedload
from database import models, db_client

router = APIRouter(prefix="/api/transactions", tags=["api"])


@router.get("/")
def api_transactions(
    db: Session = Depends(db_client.get_db),
    user: schema.UserOut = Depends(oauth2.get_current_user),
):
    transactions = (
        db.query(models.Transactions)
        .filter(models.Transactions.user_id == user.id)
        .options(joinedload(models.Transactions.category))
        .all()
    )
    return transactions


@router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=schema.Transactions
)
def insert_api_transactions(
    transaction: schema.CreateTransaction,
    db: Session = Depends(db_client.get_db),
    user: schema.UserOut = Depends(oauth2.get_current_user),
):
    print(transaction.model_dump(), user.id)
    try:
        new_transaction = models.Transactions(
            user_id=user.id, **transaction.model_dump()
        )
    except Exception as e:
        print(e)
        return None
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    return new_transaction


@router.get("/total/{type}")
def api_expense(
    type: str,
    db: Session = Depends(db_client.get_db),
    user: schema.UserOut = Depends(oauth2.get_current_user),
):
    if type not in models.Type._value2member_map_:
        return {"Error": "Expense or Income excepted in route"}
    sub_total = (
        db.query(func.sum(models.Transactions.amount))
        .filter(
            and_(models.Transactions.user_id == user.id),
            models.Transactions.type == type,
        )
        .scalar()
    )
    return {type: sub_total}
