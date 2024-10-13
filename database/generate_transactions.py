import random
from faker import Faker
from sqlalchemy.orm import Session
import models 
import db_client


def get_or_create(db: Session, table, **kwargs):
    instance = db.query(table).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = table(**kwargs)
        db.add(instance)
        db.commit()
        return instance

def create_transactions():
    db: Session = db_client.get_db()

    fake = Faker()

    user_id = 3

    categories = [
        "Bills",
        "Food",
        "Clothes",
        "Medical",
        "Housing",
        "Salary",
        "Social",
        "Transport",
        "Vacation",
    ]

    for category in categories:
        category = get_or_create(db,models.Category,name=category)

        for _ in range(2):
            fake_transaction= models.Transactions(user_id=user_id,category=category,
                                                  amount=random.uniform(1,500000),
                                                  date=fake.date_between(start_date='-1y', end_date='today'),
                                                  type=random.choice(["Income", "Expense"]))
            db.add(fake_transaction)
            db.commit()

                                                    
create_transactions()









