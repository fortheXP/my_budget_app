# services/pydantic_ai_chat_service.py - Enhanced with a Single, More Capable Agent
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel, Field
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from typing import Optional, Any, Union, Literal
from datetime import date, timedelta
from decimal import Decimal
from collections import defaultdict
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from config import GEMINI_KEY

from database.models import Category, Transactions, Type


class TransactionData(BaseModel):
    """Structured transaction data extracted from user message"""

    amount: float = Field(..., description="Transaction amount in rupees")
    category: str = Field(..., description="Transaction category")
    description: str = Field(..., description="Brief description of the transaction")
    transaction_type: Literal["Income", "Expense"] = Field(
        ..., description="Type of transaction"
    )
    transaction_date: Optional[date] = Field(
        None, description="Transaction date if mentioned"
    )


class SummaryRequest(BaseModel):
    """Structured summary request data"""

    period_days: int = Field(
        30,
        description="Number of days to analyze (1=today, 7=week, 30=month, 365=year)",
    )
    category_filter: Optional[str] = Field(
        None, description="Specific category to filter by"
    )
    transaction_type_filter: Optional[Literal["Income", "Expense"]] = Field(
        None, description="Filter by income or expense"
    )


class ConversationalResponse(BaseModel):
    """A simple conversational response"""

    response: str = Field(..., description="A friendly, conversational response")


class Deps(BaseModel):
    user_id: int
    db_session: Any


def create_gemini_model():
    provider = GoogleProvider(api_key=GEMINI_KEY)
    return GoogleModel("gemini-2.5-flash", provider=provider)


EXISTING_AGENT = None

gemini_model = create_gemini_model()
SYSTEM_PROMPT_TEMPLATE = """
You are a helpful financial assistant for a personal finance app.
Your primary job is to understand the user's message and respond with the appropriate structured data.

First, determine the user's intent.

1.  **If the user is logging a transaction (spending or receiving money)**, you MUST use the `TransactionData` format.
    -   Infer the `transaction_type` ('Income' or 'Expense') from the message.
    -   You MUST select the most appropriate category from the lists provided below.
    -   **{category_guidance}**
    -   **CRITICAL RULE: Do NOT invent a new category.** If no existing category is a good fit, you MUST use the default category:
        -   For an 'Expense' transaction, use the category: **'Miscellaneous'**
        -   For an 'Income' transaction, use the category: **'Other Income'**

2.  **If the user is asking for a summary or report**, you MUST use the `SummaryRequest` format.
    -   Infer the days from message for period_days. 
    -   Try to inter the `transaction_type_filter` ('Income' or 'Expense') from the message, if it not given  `transaction_type_filter` is None
    -   You must select a catgroy from the ones given above if no exiting category is a good fit, you can leave it None
 

3.  **For any other general financial questions or greetings**, provide a friendly response using the `ConversationalResponse` format.
"""


def get_all_categories_from_db(db: Session) -> dict[str, list[str]]:
    """Fetches all categories and organizes them by type."""
    categories_by_type = defaultdict(list)
    all_categories = db.query(Category).all()
    for cat in all_categories:
        categories_by_type[cat.type.name].append(cat.name)
    return dict(categories_by_type)


def create_agent(dynamic_prompt):
    financial_agent = Agent(
        model=gemini_model,
        output_type=Union[TransactionData, SummaryRequest, ConversationalResponse],
        system_prompt=dynamic_prompt,
    )
    return financial_agent


def get_or_create_category(
    db: Session, category_name: str, transaction_type: str
) -> Category:
    """Get existing category or create new one"""
    type_enum = Type.Income if transaction_type == "Income" else Type.Expense

    print(category_name)
    category = (
        db.query(Category)
        .filter(
            func.lower(Category.name) == func.lower(category_name),
            Category.type == type_enum.value,
        )
        .first()
    )

    if not category:
        category = Category(name=category_name, type=type_enum)
        db.add(category)
        db.commit()
        db.refresh(category)

    return category


async def process_message(user_message: str, user_id: int, db: Session):
    global EXISTING_AGENT
    deps = Deps(user_id=user_id, db_session=db)

    if not EXISTING_AGENT:
        print("--- Building and caching system prompt for the first time ---")
        categories = get_all_categories_from_db(db)
        expense_cats = categories.get("Expense", [])
        income_cats = categories.get("Income", [])

        if "miscellaneous" not in expense_cats:
            expense_cats.append("miscellaneous")
        if "other income" not in income_cats:
            income_cats.append("other income")

        category_guidance = (
            f"Available Expense Categories: {', '.join(sorted(expense_cats))}\n"
            f"    Available Income Categories: {', '.join(sorted(income_cats))}"
        )

        financial_agent = create_agent(
            SYSTEM_PROMPT_TEMPLATE.format(category_guidance=category_guidance)
        )
    try:
        response = await financial_agent.run(user_message, deps=deps)
        result_data = response.output

        if isinstance(result_data, TransactionData):
            category = get_or_create_category(
                db, result_data.category, result_data.transaction_type
            )

            new_transaction = Transactions(
                user_id=user_id,
                category_id=category.id,
                amount=Decimal(str(result_data.amount)),
                type=Type.Income
                if result_data.transaction_type == "Income"
                else Type.Expense,
                comment=result_data.description,
                date=result_data.transaction_date or date.today(),
            )

            db.add(new_transaction)
            db.commit()
            db.refresh(new_transaction)

            return f"✅ Added {result_data.transaction_type.lower()} of ₹{result_data.amount:,.2f} in {result_data.category} for '{result_data.description}'."

        elif isinstance(result_data, SummaryRequest):
            cut_off_date = date.today() - timedelta(days=result_data.period_days)
            if result_data.category_filter and result_data.transaction_type_filter:
                category = get_or_create_category(
                    db, result_data.category_filter, result_data.transaction_type_filter
                )
                summary = (
                    db.query(
                        Transactions.date,
                        Transactions.amount,
                        Transactions.type,
                        Transactions.comment,
                        Category.name.label("category"),
                    )
                    .join(Category)
                    .filter(
                        Transactions.category_id == category.id,
                        Transactions.date >= cut_off_date,
                    )
                    .all()
                )
            elif result_data.transaction_type_filter:
                summary = (
                    db.query(
                        Transactions.date,
                        Transactions.amount,
                        Transactions.type,
                        Transactions.comment,
                        Category.name.label("category"),
                    )
                    .join(Category)
                    .filter(
                        Transactions.type == result_data.transaction_type_filter,
                        Transactions.date >= cut_off_date,
                    )
                    .all()
                )
            else:
                summary = (
                    db.query(
                        Transactions.date,
                        Transactions.amount,
                        Transactions.type,
                        Transactions.comment,
                        Category.name.label("category"),
                    )
                    .join(Category)
                    .filter(
                        Transactions.date >= cut_off_date,
                    )
                    .all()
                )
            llm_input = format_for_llm(summary, "Transactions")
            print(llm_input)
            return f"Ok, I will generate a summary for the last {result_data.period_days} days."

        elif isinstance(result_data, ConversationalResponse):
            return result_data.response

        else:
            return "I'm sorry, I'm not sure how to handle that request. Please try rephrasing."

    except Exception as e:
        print(f"An error occurred: {e}")
        return "I'm sorry, I wasn't able to process that. Could you please try rephrasing it?"


def format_for_llm(records, table_name="Records"):
    """Most reliable version that works with any SQLAlchemy result"""
    if not records:
        return f"No {table_name.lower()} found."

    output = f"{table_name} Data Summary:\n"
    output += f"Total records: {len(records)}\n\n"

    for i, record in enumerate(records, 1):
        output += f"Record {i}:\n"

        # Handle different types of records
        if hasattr(record, "_fields"):  # Named tuple
            for field in record._fields:
                value = getattr(record, field)
                output += f"  - {field}: {value}\n"

        elif hasattr(record, "keys"):  # Row object
            for key in record.keys():
                value = record[key]
                output += f"  - {key}: {value}\n"

        elif hasattr(record, "__table__"):  # Model instance
            for col in record.__table__.columns:
                value = getattr(record, col.key)
                output += f"  - {col.key}: {value}\n"

        else:  # Fallback - convert to string
            output += f"  - data: {record}\n"

        output += "\n"

    return output
