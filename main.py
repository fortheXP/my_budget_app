from fastapi import FastAPI, HTTPException, Depends, Response, status, Request, Form 
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from db_client import Budget_db
from database import models, db_client
from typing import Annotated, Optional
from pathlib import Path
from app.routers.api import api_users,api_transactions
import schema
from app import utils, oauth2

app = FastAPI()
app.include_router(api_users.router)
app.include_router(api_transactions.router)

app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent.absolute() / "static"),
    name="static",
)


def get_db():
    return Budget_db()


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
    db: Session = Depends(db_client.get_db)
): 
    user = schema.UserCreate(username=username,password=password)
    user.password = utils.get_password_hash(user.password)
    new_user = models.User(**user.model_dump())
    db.add(new_user)
    db.commit()
    return templates.TemplateResponse(
            "home.html",
            {"request": request},
        )

@app.post("/login")
def login_user(request: Request,
    response: Response,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    db: Session = Depends(db_client.get_db)
): 
    user = oauth2.authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request" : request, "message": "Incorrect Username or Password"}
        )

    access_token = oauth2.create_auth_token({"sub": user.id})
    response = RedirectResponse(url='/dashboard', status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}",httponly=True)
    return response




@app.get("/dashboard")
def dashboard(request: Request, user: schema.UserOut = Depends(oauth2.get_user)):
    if user is None:
        return templates.TemplateResponse(
            "login.html",
            {"request" : request, "message": "Session Expired, Please Login again"}
        )

    return templates.TemplateResponse(
        "dashboard.html",
        {"request" : request, "user": user}
    )
@app.get("/logout")
def logout(response: Response):
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response

@app.get("/transactions")
def transactions(request: Request,db: Session = Depends(db_client.get_db), user: schema.UserOut = Depends(oauth2.get_user)):
    if user is None:
        return templates.TemplateResponse(
            "login.html",
            {"request" : request, "message": "Session Expired, Please Login again"}
        )
    transactions = db.query(models.Transactions).filter(models.Transactions.user_id==user.id).options(joinedload(models.Transactions.category)).all()
    return templates.TemplateResponse(
        "transactions.html",
        {"request" : request, "user" : user ,"transactions": transactions}
    )
@app.post("/transactions/filter")
def filter_transactions(request: Request, type: Annotated[str, Form()],db: Session = Depends(db_client.get_db), user: schema.UserOut = Depends(oauth2.get_user)):
    if user is None:
        return templates.TemplateResponse(
            "login.html",
            {"request" : request, "message": "Session Expired, Please Login again"}
        )
    print(type)
    if type=="Any":
        transactions = db.query(models.Transactions).filter(models.Transactions.user_id==user.id).options(joinedload(models.Transactions.category)).all()
    else:
        transactions = db.query(models.Transactions).filter(and_(models.Transactions.user_id==user.id),models.Transactions.type==type).options(joinedload(models.Transactions.category)).all()
    return templates.TemplateResponse(
        "table-contents.html",
        {"request" : request, "user" : user ,"transactions": transactions}
    )

@app.get("/api")
def root():
    return {"Happy": "Budgeting"}






@app.post("/api/budgets", status_code=status.HTTP_201_CREATED)
def insert(
    item: schema.item,
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


@app.get("/api/budgets/{id}")
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


@app.get("/budgets/month")
def budget_current_month(db: Budget_db = Depends(get_db)):
    try:
        budget_of_current_month = db.get_month_budget()
        return budget_of_current_month
    except Exception as e:
        print(f"get_by_id: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.delete("/api/budgets/{id}", status_code=status.HTTP_204_NO_CONTENT)
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


@app.delete("/budgets/{id}", status_code=status.HTTP_200_OK)
def delete_budget_table(
    request: Request,
    id: int,
    db: Budget_db = Depends(get_db),
):
    try:
        db.delete(id)
        budgets = main(db=get_db())
        expense = budget_current_month(db=get_db())
        return templates.TemplateResponse(
            "table.html",
            {"request": request, "entries": budgets, "expense": expense["Expense"]},
        )
    except Exception as e:
        print(f"Delete Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
