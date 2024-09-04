import sqlite3
from datetime import datetime


def dict_factory(cur, row):
    fields = [column[0] for column in cur.description]
    return {key: value for key, value in zip(fields, row)}


class Budget_db:
    def __init__(self):
        self.con = sqlite3.connect("budget.db", check_same_thread=False)
        self.con.row_factory = dict_factory
        self.cur = self.con.cursor()
        self.table

    @property
    def table(self):
        self.cur.execute(
            "CREATE TABLE IF NOT EXISTS my_budget(id INTEGER PRIMARY KEY AUTOINCREMENT,date TEXT, credit_or_debit TEXT CHECK(credit_or_debit in ('CRE','DEB')),amount NUMERIC, category TEXT, comments TEXT)"
        )

    def select_all(self):
        res = self.cur.execute("SELECT * FROM my_budget order by id DESC LIMIT 10 ")
        return res.fetchall()

    def insert(
        self,
        date: str,
        credit_or_debit: str,
        amount: float,
        category: str,
        comments=None,
    ):
        self.cur.execute(
            "INSERT INTO  my_budget(date,credit_or_debit,amount,category,comments) VALUES (?,?,?,?,?)",
            (date, credit_or_debit, amount, category, comments),
        )
        self.con.commit()

    def get_by_id(self, id: int):
        res = self.cur.execute("SELECT * FROM my_budget WHERE id = (?)", (id,))
        return res.fetchone()

    def delete(self, id: int):
        self.cur.execute("DELETE FROM my_budget WHERE id = (?)", (id,))
        self.con.commit()

    def get_month_budget(self):
        first_date = datetime.today().replace(day=1)
        formated_date = first_date.strftime("%Y-%m-%d")
        res = self.cur.execute(
            "SELECT SUM(CASE WHEN credit_or_debit='CRE' THEN amount ELSE 0 END) as Income,SUM(CASE WHEN credit_or_debit='DEB' THEN amount ELSE 0 END) as Expense ,SUM(CASE WHEN credit_or_debit='CRE' THEN amount ELSE -amount END) as Remaining FROM my_budget WHERE date >= (?)",
            (formated_date,),
        )
        return res.fetchone()
