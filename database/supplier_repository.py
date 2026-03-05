from database.base_repository import BaseRepository


class SupplierRepository(BaseRepository):
    def __init__(self):
        super().__init__("suppliers")
        self.create_table({
            "ID": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "name": "TEXT NOT NULL",
            "description": "TEXT DEFAULT ''",
            "email": "TEXT DEFAULT ''",
            "phone": "TEXT DEFAULT ''",
            "address": "TEXT DEFAULT ''",
            "authorized_person": "TEXT DEFAULT ''",
            "IBAN": "TEXT DEFAULT ''",
            "logo": "TEXT DEFAULT ''",
            "image_data": "TEXT DEFAULT ''",
            "is_active": "INTEGER DEFAULT 1",
            "created_at": "TEXT NOT NULL"
        })
        self._ensure_column("image_data", "TEXT DEFAULT ''")

    def get_by_name(self, name: str) -> list[dict]:
        return self.get_by_field("name", name)

    def search_by_name(self, keyword: str) -> list[dict]:
        return self.search("name", keyword)

    def get_active_suppliers(self) -> list[dict]:
        return self.get_by_field("is_active", 1)