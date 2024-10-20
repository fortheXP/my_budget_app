import schema
from fastapi import Depends, status, APIRouter, HTTPException 
from app import oauth2
from sqlalchemy.orm import Session, joinedload
from database import models, db_client
router = APIRouter(prefix="/api/transactions", tags=["api"])

@router.get("/")
def api_transactions(db: Session = Depends(db_client.get_db), user: schema.UserOut = Depends(oauth2.get_current_user)):
    transactions = db.query(models.Transactions).filter(models.Transactions.user_id==user.id).options(joinedload(models.Transactions.category)).all()
    return transactions
