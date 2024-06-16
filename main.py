from db_client import Budget_db


def main():
    print("welcome to my budget app")
    budgetdb = Budget_db()
#    budgetdb.insert('2024-06-16','CRE',70000,'Salary')
    print(budgetdb.select_all())


if __name__ == "__main__":
    main()
