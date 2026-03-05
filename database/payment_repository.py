from database.base_repository import BaseRepository

class PaymentRepository(BaseRepository):
    def __init__(self):
        super().__init__("payments")
        self.create_table({
            "ID": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "order_ID": "INTEGER NOT NULL REFERENCES orders(ID)",
            "method": "TEXT NOT NULL",
            "amount": "REAL NOT NULL",
            "status": "TEXT DEFAULT ''",
            "payment_date": "TEXT DEFAULT NULL",
            "note": "TEXT DEFAULT ''"
        })

    def get_by_order(self, order_id: int) -> list[dict]:
        return self.get_by_field("order_ID", order_id)

    def get_by_method(self, method: str) -> list[dict]:
        return self.get_by_field("method", method)

    def get_by_status(self, status: str) -> list[dict]:
        return self.get_by_field("status", status)

    def get_order_paid_total(self, order_id: int) -> float:
        query = f"SELECT SUM(amount) as total FROM {self.table_name} WHERE order_ID = ? AND status = 'completed'"
        result = self.db.fetch_one(query, (order_id,))
        return result["total"] if result and result["total"] else 0.0

    def get_by_date_range(self, start_date: str, end_date: str) -> list[dict]:
        query = f"""
            SELECT * FROM {self.table_name} 
            WHERE payment_date BETWEEN ? AND ?
            ORDER BY payment_date DESC
        """
        return self.db.fetch_all(query, (start_date, end_date))