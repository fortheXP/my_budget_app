from fastapi import FastAPI, HTTPException, Depends, status, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from db_client import Budget_db
from typing import Annotated, Optional

import schema


app = FastAPI()


def get_db():
    return Budget_db()


templates = Jinja2Templates("templates")


@app.get("/")
def root_index(request: Request):
    accept_header = request.headers.get("Accept")
    if accept_header and "text/html" in accept_header:
        budgets = main(db=get_db())
        expense = budget_current_month(db=get_db())
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "entries": budgets, "expense": expense["Expense"]},
        )
    return {"Happy": "Budgeting"}


@app.get("/api")
def root():
    return {"Happy": "Budgeting"}


@app.get("/budgets")
def table_view(request: Request, db: Budget_db = Depends(get_db)):
    try:
        budgets = db.select_all()
        accept_header = request.headers.get("Accept")
        if accept_header and "text/html" in accept_header:
            return templates.TemplateResponse(
                "table.html", {"request": request, "entries": budgets}
            )
        return budgets
    except Exception as e:
        print(f"Selectall Error : {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.get("/api/budgets")
def main(db: Budget_db = Depends(get_db)):
    try:
        budgets = db.select_all()
        return budgets
    except Exception as e:
        print(f"Selectall Error : {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.post("/budgets/insert", response_class=HTMLResponse)
def form_insert(
    request: Request,
    date: Annotated[str, Form()],
    credit_or_debit: Annotated[str, Form()],
    amount: Annotated[float, Form()],
    category: Annotated[str, Form()],
    comments: Optional[str] = Form(None),
    db: Budget_db = Depends(get_db),
):
    try:
        db.insert(date, credit_or_debit, amount, category, comments)
        budgets = main(db=get_db())
        expense = budget_current_month(db=get_db())
        return templates.TemplateResponse(
            "table.html", {"request": request, "entries": budgets, "expense": expense["Expense"] }
        )
    except Exception as e:
        print(f"Insert Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


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
