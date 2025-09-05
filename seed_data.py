#!/usr/bin/env python3
"""
Database seeding script to populate initial data
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database.models import Base, Category, Type
from config import DATABASE_URL


def create_categories(session):
    """Create initial categories if they don't exist"""

    # Default expense categories
    expense_categories = [
        "Food & Dining",
        "Transportation",
        "Shopping",
        "Entertainment",
        "Bills & Utilities",
        "Healthcare & Medical",
        "Education",
        "Travel",
        "Miscellaneous",
    ]

    # Default income categories
    income_categories = [
        "Salary",
        "Freelance",
        "Business Income",
        "Investments",
        "Gifts",
        "Other Income",
    ]

    categories_created = 0

    # Create expense categories
    for cat_name in expense_categories:
        existing = (
            session.query(Category)
            .filter(Category.name == cat_name, Category.type == Type.Expense)
            .first()
        )

        if not existing:
            category = Category(name=cat_name, type=Type.Expense)
            session.add(category)
            categories_created += 1
            print(f"Created expense category: {cat_name}")
        else:
            print(f" Expense category already exists: {cat_name}")

    # Create income categories
    for cat_name in income_categories:
        existing = (
            session.query(Category)
            .filter(Category.name == cat_name, Category.type == Type.Income)
            .first()
        )

        if not existing:
            category = Category(name=cat_name, type=Type.Income)
            session.add(category)
            categories_created += 1
            print(f"Created income category: {cat_name}")
        else:
            print(f"Income category already exists: {cat_name}")

    return categories_created


def main():
    """Main seeding function"""
    try:
        print(f"onnecting to database: {DATABASE_URL}")

        # Create engine and session
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()

        print("tarting database seeding...")

        # Create categories
        categories_created = create_categories(session)

        # Commit changes
        session.commit()

        print(
            f"Database seeding completed! Created {categories_created} new categories."
        )

        # Verify data
        total_categories = session.query(Category).count()
        expense_count = (
            session.query(Category).filter(Category.type == Type.Expense).count()
        )
        income_count = (
            session.query(Category).filter(Category.type == Type.Income).count()
        )

        print(f"atabase summary:")
        print(f"Total categories: {total_categories}")
        print(f"Expense categories: {expense_count}")
        print(f"Income categories: {income_count}")

        session.close()
        return 0

    except Exception as e:
        print(f"Error during database seeding: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
