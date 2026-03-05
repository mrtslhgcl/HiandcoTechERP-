from database.base_repository import BaseRepository

class OrderItemRepository(BaseRepository):
    def __init__(self):
        super().__init__("order_items")
        self.create_table({
            "ID": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "order_ID": "INTEGER NOT NULL REFERENCES orders(ID)",
            "product_ID": "INTEGER NOT NULL",
            "variant_ID": "INTEGER NOT NULL",
            "quantity": "INTEGER DEFAULT 1",
            "unit_price": "REAL DEFAULT 0.0",
            "product_name": "TEXT DEFAULT ''"
        })

    def get_by_order(self, order_id: int) -> list[dict]:
        return self.get_by_field("order_ID", order_id)

    def get_by_product(self, product_id: int) -> list[dict]:
        return self.get_by_field("product_ID", product_id)

    def get_by_variant(self, variant_id: int) -> list[dict]:
        return self.get_by_field("variant_ID", variant_id)

    def get_order_total(self, order_id: int) -> float:
        query = f"SELECT SUM(quantity * unit_price) as total FROM {self.table_name} WHERE order_ID = ?"
        result = self.db.fetch_one(query, (order_id,))
        return result["total"] if result and result["total"] else 0.0