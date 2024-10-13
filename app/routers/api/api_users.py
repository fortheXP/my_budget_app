import schema
from fastapi import Depends, status, APIRouter, HTTPException
from fastapi.security.oauth2 import OAuth2PasswordRequestForm

from sqlalchemy.orm import Session
from database import models, db_client
from app import oauth2, utils

router = APIRouter(prefix="/api/users", tags=["api"])




@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schema.UserOut)
def create_user(user: schema.UserCreate, db: Session = Depends(db_client.get_db)):
    user.password = utils.get_password_hash(user.password)
    new_user = models.User(**user.model_dump())
    db.add(new_user)
    db.commit()
    return new_user


@router.get("/me", status_code=status.HTTP_200_OK, response_model=schema.UserOut)
def get_user(user: schema.UserOut = Depends(oauth2.get_current_user)):
    return user


@router.post("/auth")
def auth(
    user_cred: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(db_client.get_db),
):
    user = oauth2.authenticate_user(db, user_cred.username, user_cred.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = oauth2.create_auth_token({"sub": user.id})
    return schema.Token(access_token=access_token, token_type="bearer")
