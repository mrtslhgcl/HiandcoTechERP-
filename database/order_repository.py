from database.base_repository import BaseRepository

class OrderRepository(BaseRepository):
    def __init__(self):
        super().__init__("orders")
        self.create_table({
            "ID": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "customer_ID": "INTEGER DEFAULT 0",
            "currency": "TEXT DEFAULT 'TRY'",
            "created_at": "TEXT NOT NULL",
            "shipping_address": "TEXT DEFAULT 'In-store Pickup'",
            "billing_address": "TEXT DEFAULT 'In-store Pickup'",
            "status": "TEXT DEFAULT 'pending'",
            "tracking_number": "TEXT DEFAULT ''",
            "delivery_date": "TEXT DEFAULT NULL",
            "refund_price": "REAL DEFAULT 0.0",
            "refund_reason": "TEXT DEFAULT ''",
            "refund_history": "TEXT DEFAULT '[]'",
            "cancellation_reason": "TEXT DEFAULT ''",
            "cancellation_date": "TEXT DEFAULT NULL",
            "notes": "TEXT DEFAULT ''",
            "is_gift": "INTEGER DEFAULT 0",
            "gift_message": "TEXT DEFAULT ''",
            "discount_code": "TEXT DEFAULT ''",
            "discount_price": "REAL DEFAULT 0.0",
            "total_weight": "REAL DEFAULT 0.0",
            "total_volume": "REAL DEFAULT 0.0"
        })

    def get_by_customer(self, customer_id: int) -> list[dict]:
        return self.get_by_field("customer_ID", customer_id)

    def get_by_status(self, status: str) -> list[dict]:
        return self.get_by_field("status", status)

    def get_by_date_range(self, start_date: str, end_date: str) -> list[dict]:
        query = f"""
            SELECT * FROM {self.table_name} 
            WHERE created_at BETWEEN ? AND ?
            ORDER BY created_at DESC
        """
        return self.db.fetch_all(query, (start_date, end_date))

    def get_pending_orders(self) -> list[dict]:
        return self.get_by_status("pending")

    def get_cancelled_orders(self) -> list[dict]:
        return self.get_by_status("cancelled")

    def get_refunded_orders(self) -> list[dict]:
        query = f"SELECT * FROM {self.table_name} WHERE refund_price > 0"
        return self.db.fetch_all(query)

    def update_status(self, order_id: int, status: str) -> bool:
        return self.update(order_id, {"status": status})