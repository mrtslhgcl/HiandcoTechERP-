from database.base_repository import BaseRepository


class CustomerRepository(BaseRepository):
    def __init__(self):
        super().__init__("customers")
        self.create_table({
            "ID": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "first_name": "TEXT NOT NULL",
            "last_name": "TEXT NOT NULL",
            "email": "TEXT DEFAULT ''",
            "phone_number": "TEXT DEFAULT ''",
            "address": "TEXT DEFAULT ''",
            "notes": "TEXT DEFAULT ''",
            "is_active": "INTEGER DEFAULT 1",
            "created_at": "TEXT NOT NULL"
        })

    def get_by_email(self, email: str) -> dict | None:
        results = self.get_by_field("email", email)
        return results[0] if results else None

    def get_by_phone(self, phone_number: str) -> dict | None:
        results = self.get_by_field("phone_number", phone_number)
        return results[0] if results else None

    def get_active_customers(self) -> list[dict]:
        return self.get_by_field("is_active", 1)

    def search_by_name(self, keyword: str) -> list[dict]:
        query = f"SELECT * FROM {self.table_name} WHERE first_name LIKE ? OR last_name LIKE ?"
        return self.db.fetch_all(query, (f"%{keyword}%", f"%{keyword}%"))