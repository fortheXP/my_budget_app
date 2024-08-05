import sqlite3


class Budget_db:
    def __init__(self):
        self.con = sqlite3.connect("budget.db", check_same_thread=False)
        self.cur = self.con.cursor()
        self.table

    @property
    def table(self):
        res = self.cur.execute("SELECT name FROM sqlite_master WHERE name='my_budget'")
        if res.fetchone() is None:
            self.cur.execute(
                "CREATE TABLE my_budget(id INTEGER PRIMARY KEY AUTOINCREMENT,date TEXT, credit_or_debit TEXT CHECK(credit_or_debit in ('CRE','DEB')),amount NUMERIC, category TEXT, comments TEXT)"
            )

    def select_all(self):
        res = self.cur.execute("SELECT * FROM my_budget ")
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
