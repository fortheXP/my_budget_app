from fastapi import (
    FastAPI,
    Request,
    Response,
    status,
    Depends,
    Form,
    HTTPException,
    WebSocket,
)
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from decimal import Decimal
from datetime import date
from typing import Annotated, Optional
from pathlib import Path
import json

from database import models, db_client
from database.models import Type
import schema
from app import utils, oauth2
from app.services.pydantic_ai_chat_service import process_message


def create_app() -> FastAPI:
    app = FastAPI()

    app.mount(
        "/static",
        StaticFiles(directory=Path(__file__).parent.parent / "static"),
        name="static",
    )

    templates = Jinja2Templates("templates")

    @app.middleware("http")
    async def force_https_urls(request: Request, call_next):
        if request.headers.get("x-forwarded-proto") == "https":
            request.scope["scheme"] = "https"
        response = await call_next(request)
        return response

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
        current_category_id: Annotated[Optional[int], Form()] = None,
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

        current_category_exists = (
            any(cat.id == current_category_id for cat in categories)
            if current_category_id
            else False
        )

        return templates.TemplateResponse(
            "category_option.html",
            {
                "request": request,
                "categories": categories,
                "current_category_id": current_category_id,
                "current_category_exists": current_category_exists,
            },
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
    def signup_post(
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
    def login_post(
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
        response = RedirectResponse(
            url="/dashboard", status_code=status.HTTP_303_SEE_OTHER
        )
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
            .order_by(models.Transactions.date.desc())
            .limit(10)
            .all()
        )
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
        return templates.TemplateResponse(
            "insert.html", {"request": request, "user": user}
        )

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
            trans = schema.CreateTransaction(
                date=date,
                type=in_or_exp,
                user_id=user.id,
                amount=amount,
                category_id=category,
                comment=comments,
            )
            new_trans = models.Transactions(**trans.model_dump())
            db.add(new_trans)
            db.commit()

            return templates.TemplateResponse(
                "form.html", {"request": request, "user": user}
            )
        except Exception as e:
            print(f"Insert Error: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    @app.get("/transactions/{id}", response_class=HTMLResponse)
    def get_transaction(
        request: Request,
        user: schema.UserOut = Depends(oauth2.get_user),
        db: Session = Depends(db_client.get_db),
        id: int = 0,
    ):
        if user is None:
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "message": "Session Expired, Please Login again"},
            )
        transaction = (
            db.query(models.Transactions)
            .filter(
                and_(models.Transactions.user_id == user.id),
                models.Transactions.id == id,
            )
            .first()
        )
        if transaction is None:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return templates.TemplateResponse(
            "transaction.html",
            {"request": request, "user": user, "transaction": transaction},
        )

    @app.post("/transactions/{transaction_id}", response_class=HTMLResponse)
    def update_transaction(
        request: Request,
        transaction_id: int,
        date: Annotated[date, Form()],
        in_or_exp: Annotated[str, Form()],
        amount: Annotated[float, Form()],
        category: Annotated[Optional[int], Form()] = None,
        db: Session = Depends(db_client.get_db),
        user: schema.UserOut = Depends(oauth2.get_user),
    ):
        if user is None:
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "message": "Session Expired, Please Login again"},
            )

        transaction = db.get(models.Transactions, transaction_id)
        if transaction is None:
            raise HTTPException(status_code=404, detail="Transaction not found")

        if transaction.user_id != user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        transaction.date = date
        transaction.type = Type(in_or_exp)
        transaction.amount = Decimal(str(amount))
        transaction.category_id = category

        db.commit()

        return templates.TemplateResponse(
            "transaction.html",
            {"request": request, "user": user, "transaction": transaction},
        )

    @app.delete("/transactions/{transaction_id}")
    def delete_transaction(
        request: Request,
        transaction_id: int,
        user: schema.UserOut = Depends(oauth2.get_user),
        db: Session = Depends(db_client.get_db),
    ):
        if user is None:
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "message": "Session Expired, Please Login again"},
            )
        transaction = db.get(models.Transactions, transaction_id)
        if transaction is None:
            raise HTTPException(status_code=404, detail="Transaction not found")

        if transaction.user_id != user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        db.delete(transaction)
        db.commit()
        return Response(status_code=200)

    @app.get("/transactions/{transaction_id}/edit", response_class=HTMLResponse)
    def edit_transaction(
        request: Request,
        transaction_id: int,
        user: schema.UserOut = Depends(oauth2.get_user),
        db: Session = Depends(db_client.get_db),
    ):
        if user is None:
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "message": "Session Expired, Please Login again"},
            )
        transaction = (
            db.query(models.Transactions)
            .filter(
                and_(models.Transactions.user_id == user.id),
                models.Transactions.id == transaction_id,
            )
            .first()
        )
        if transaction is None:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return templates.TemplateResponse(
            "transaction-edit.html",
            {"request": request, "user": user, "transaction": transaction},
        )

    @app.get("/chat", response_class=HTMLResponse)
    def get_chat(request: Request, user: schema.UserOut = Depends(oauth2.get_user)):
        if user is None:
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "message": "Session Expired, Please Login again"},
            )
        return templates.TemplateResponse(
            "chat.html",
            {"request": request, "user": user},
        )

    @app.websocket("/ws")
    async def websocket_connection(
        websocket: WebSocket,
        user: schema.UserOut = Depends(oauth2.get_user),
        db: Session = Depends(db_client.get_db),
    ):
        await websocket.accept()
        while True:
            try:
                data = await websocket.receive_text()
                parsed = json.loads(data)
                user_msg = parsed.get("message", "").strip()
                user_html = templates.env.get_template("chat_partial.html").render(
                    {"message_text": user_msg, "is_system": False}
                )
                await websocket.send_text(user_html)

                system_response = await process_message(user_msg, user.id, db)
                response_html = templates.get_template("chat_partial.html").render(
                    {"message_text": system_response, "is_system": True}
                )
                await websocket.send_text(response_html)

            except Exception as e:
                print(e)
                await websocket.close()
                break

    @app.get("/api")
    def root():
        return {"Happy": "Budgeting"}

    return app
