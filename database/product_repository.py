from database.base_repository import BaseRepository


class ProductRepository(BaseRepository):
    def __init__(self):
        super().__init__("products")
        self.create_table({
            "ID": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "name": "TEXT NOT NULL",
            "description": "TEXT DEFAULT ''",
            "main_category_ID": "INTEGER DEFAULT NULL REFERENCES categories(ID)",
            "extra_category_IDs": "TEXT DEFAULT '[]'",
            "brand_ID": "INTEGER DEFAULT NULL REFERENCES brands(ID)",
            "supplier_ID": "INTEGER DEFAULT NULL REFERENCES suppliers(ID)",
            "sale_unit": "TEXT DEFAULT 'ADET'",
            "is_active": "INTEGER DEFAULT 1",
            "created_at": "TEXT NOT NULL"
        })

    def get_by_name(self, name: str) -> list[dict]:
        return self.get_by_field("name", name)

    def search_by_name(self, keyword: str) -> list[dict]:
        return self.search("name", keyword)

    def get_by_brand(self, brand_id: int) -> list[dict]:
        return self.get_by_field("brand_ID", brand_id)

    def get_by_supplier(self, supplier_id: int) -> list[dict]:
        return self.get_by_field("supplier_ID", supplier_id)

    def get_by_category(self, category_id: int) -> list[dict]:
        return self.get_by_field("main_category_ID", category_id)

    def get_by_any_category(self, category_id: int) -> list[dict]:
        query = f"""
            SELECT * FROM {self.table_name} 
            WHERE main_category_ID = ? 
            OR extra_category_IDs LIKE ?
        """
        return self.db.fetch_all(query, (category_id, f"%{category_id}%"))

    def get_active_products(self) -> list[dict]:
        return self.get_by_field("is_active", 1)

    def get_inactive_products(self) -> list[dict]:
        return self.get_by_field("is_active", 0)