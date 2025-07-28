from datetime import datetime, timedelta, timezone
from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security.oauth2 import OAuth2PasswordBearer
import jwt
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session
from app import utils
from database import models, db_client
import schema

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/users/auth")

SECRET_KEY = "4d738a2afc1ceff0627a7cba206af7c56ff4b688249139da901eda4fcf1f11ce"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def authenticate_user(db: Session, username: str, password: str):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        return False
    if not utils.verify_password(password, user.password):
        return False
    return user


def create_auth_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_auth_token(token: str, credentials_exception: HTTPException):
    try:
        print(token)
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        id = payload.get("sub")
        token = schema.Token_Data(id=id)
        return token
    except Exception as e:
        print(f"error: {e}")
        raise credentials_exception


def get_user(access_token: str = Cookie(None), db: Session = Depends(db_client.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        access_token = str.replace(str(access_token), "Bearer ", "")
        print(access_token)
        token = verify_auth_token(access_token, credentials_exception)
        print(token.id)
        user = db.query(models.User).filter(models.User.id == token.id).first()
        print(user)
        if user is None:
            return credentials_exception
        return user
    except HTTPException:
        return None


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(db_client.get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = verify_auth_token(token, credentials_exception)
    user = db.query(models.User).filter(models.User.id == token.id).first()
    if user is None:
        raise credentials_exception
    return user
