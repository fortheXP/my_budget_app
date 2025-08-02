import enum
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, relationship
from database.db_client import Base, engine
from datetime import date


class Type(enum.Enum):
    Income = "Income"
    Expense = "Expense"


class User(Base):
    __tablename__ = "users"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    username = sa.Column(sa.String, unique=True, index=True, nullable=False)
    password = sa.Column(sa.String, nullable=False)


class Category(Base):
    __tablename__ = "category"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    name = sa.Column(sa.String, unique=True, nullable=True)
    type = sa.Column(sa.Enum(Type), nullable=False, index=True)
    transactions = relationship("Transactions", back_populates="category")


class Transactions(Base):
    __tablename__ = "transactions"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    user_id = sa.Column(
        sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    category_id = sa.Column(
        sa.Integer, sa.ForeignKey("category.id", ondelete="CASCADE"), nullable=False
    )
    amount = sa.Column(sa.Numeric(10, 2), nullable=False)
    category = relationship("Category", back_populates="transactions")
    type = sa.Column(sa.Enum(Type), nullable=False)
    comment = sa.Column(sa.String)
    date = sa.Column(sa.Date, nullable=False, default=date.today)
