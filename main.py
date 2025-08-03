from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    Response,
    status,
    Request,
    Form,
)
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from database import models, db_client
from typing import Annotated, Optional
from pathlib import Path
from app.routers.api import api_users, api_transactions
import schema
from app import utils, oauth2
from datetime import date

app = FastAPI()
app.include_router(api_users.router)
app.include_router(api_transactions.router)

app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent.absolute() / "static"),
    name="static",
)


templates = Jinja2Templates("templates")


@app.get("/")
def root_index(request: Request):
    accept_header = request.headers.get("Accept")
    if accept_header and "text/html" in accept_header:
        return templates.TemplateResponse(
            "home.html",
            {"request": request},
        )
    return {"Happy": "Budgeting"}


@app.get("/signup")
def signup(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@app.get("/login")
def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/check_username", response_class=HTMLResponse)
def check_username(
    request: Request,
    username: Annotated[str, Form()],
    db: Session = Depends(db_client.get_db),
):
    print(username)
    if db.query(models.User).filter(models.User.username == username).first():
        return HTMLResponse(
            "<div id='username_result' style='color: green;'>Username already exists</div>"
        )
    else:
        return HTMLResponse(
            "<div id='username_result' style='color: green;'>Username available</div>"
        )


@app.post("/get_category", response_class=HTMLResponse)
def get_category(
    request: Request,
    in_or_exp: Annotated[str, Form()],
    db: Session = Depends(db_client.get_db),
    user: schema.UserOut = Depends(oauth2.get_user),
):
    if user is None:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "message": "Session Expired, Please Login again"},
        )
    categories = (
        db.query(models.Category).filter(models.Category.type == in_or_exp).all()
    )

    return templates.TemplateResponse(
        "category_option.html",
        {"request": request, "categories": categories},
    )


@app.post("/password_check", response_class=HTMLResponse)
def password_check(
    request: Request,
    password: Annotated[str, Form()],
    confirmPassword: Annotated[str, Form()],
):
    if password != confirmPassword:
        return HTMLResponse(
            '<div id="password_check"> Password not matching  <button type="submit" disabled class="btn signup-btn w-100">Sign Up</button></div>'
        )

    else:
        return HTMLResponse(
            '<div id="password_check"><button type="submit" class="btn signup-btn w-100">Sign Up</button></div>'
        )


@app.post("/signup")
def sigup(
    request: Request,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    confirmPassword: Annotated[str, Form()],
    db: Session = Depends(db_client.get_db),
):
    user = schema.UserCreate(username=username, password=password)
    user.password = utils.get_password_hash(user.password)
    new_user = models.User(**user.model_dump())
    db.add(new_user)
    db.commit()
    return templates.TemplateResponse(
        "home.html",
        {"request": request},
    )


@app.post("/login")
def login_user(
    request: Request,
    response: Response,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    db: Session = Depends(db_client.get_db),
):
    user = oauth2.authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "message": "Incorrect Username or Password"},
        )

    access_token = oauth2.create_auth_token({"sub": user.id})
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token", value=f"Bearer {access_token}", httponly=True
    )
    return response


@app.get("/dashboard")
def dashboard(request: Request, user: schema.UserOut = Depends(oauth2.get_user)):
    if user is None:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "message": "Session Expired, Please Login again"},
        )

    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "user": user}
    )


@app.get("/logout")
def logout(response: Response):
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response


@app.get("/transactions")
def transactions(
    request: Request,
    db: Session = Depends(db_client.get_db),
    user: schema.UserOut = Depends(oauth2.get_user),
):
    if user is None:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "message": "Session Expired, Please Login again"},
        )
    transactions = (
        db.query(models.Transactions)
        .filter(models.Transactions.user_id == user.id)
        .options(joinedload(models.Transactions.category))
        .limit(10)
        .all()
    )
    print(transactions)
    return templates.TemplateResponse(
        "transactions.html",
        {"request": request, "user": user, "transactions": transactions},
    )


@app.get("/transactions/insert")
def transactions_insert(
    request: Request,
    db: Session = Depends(db_client.get_db),
    user: schema.UserOut = Depends(oauth2.get_user),
):
    if user is None:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "message": "Session Expired, Please Login again"},
        )
    return templates.TemplateResponse("insert.html", {"request": request, "user": user})


@app.post("/transactions/insert")
def insert_transaction(
    request: Request,
    date: Annotated[date, Form()],
    in_or_exp: Annotated[str, Form()],
    amount: Annotated[float, Form()],
    category: Annotated[int, Form()],
    comments: Annotated[Optional[str], Form()] = None,
    db: Session = Depends(db_client.get_db),
    user: schema.UserOut = Depends(oauth2.get_user),
):
    if user is None:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "message": "Session Expired, Please Login again"},
        )
    try:
        print(category)

        trans = schema.CreateTransaction(
            date=date,
            type=in_or_exp,
            user_id=user.id,
            amount=amount,
            category_id=category,
            comment=comments,
        )
        new_trans = models.Transactions(**trans.dict())
        db.add(new_trans)
        db.commit()

        return templates.TemplateResponse(
            "form.html", {"request": request, "user": user}
        )
    except Exception as e:
        print(f"Insert Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.post("/transactions/filter")
def filter_transactions(
    request: Request,
    type: Annotated[str, Form()],
    db: Session = Depends(db_client.get_db),
    user: schema.UserOut = Depends(oauth2.get_user),
):
    if user is None:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "message": "Session Expired, Please Login again"},
        )
    print(type)
    if type == "Any":
        transactions = (
            db.query(models.Transactions)
            .filter(models.Transactions.user_id == user.id)
            .options(joinedload(models.Transactions.category))
            .limit(10)
            .all()
        )
    else:
        transactions = (
            db.query(models.Transactions)
            .filter(
                and_(models.Transactions.user_id == user.id),
                models.Transactions.type == type,
            )
            .options(joinedload(models.Transactions.category))
            .all()
        )
    return templates.TemplateResponse(
        "table-contents.html",
        {"request": request, "user": user, "transactions": transactions},
    )


@app.get("/api")
def root():
    return {"Happy": "Budgeting"}
