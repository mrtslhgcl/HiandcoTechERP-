from database.base_repository import BaseRepository

class EmployeeRepository(BaseRepository):
    def __init__(self):
        super().__init__("employees")
        self.create_table({
            "ID": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "employee_code": "TEXT NOT NULL UNIQUE",
            "first_name": "TEXT NOT NULL",
            "last_name": "TEXT NOT NULL",
            "photo_path": "TEXT DEFAULT ''",
            "image_data": "TEXT DEFAULT ''",
            "status": "INTEGER DEFAULT 1",
            "created_at": "TEXT NOT NULL",
            "email": "TEXT DEFAULT ''",
            "phone_number": "TEXT DEFAULT ''",
            "address": "TEXT DEFAULT ''",
            "notes": "TEXT DEFAULT ''"
        })
        self._ensure_column("image_data", "TEXT DEFAULT ''")

    def get_by_code(self, employee_code: str) -> dict | None:
        results = self.get_by_field("employee_code", employee_code)
        return results[0] if results else None

    def get_active_employees(self) -> list[dict]:
        return self.get_by_field("status", 1)

    def get_inactive_employees(self) -> list[dict]:
        return self.get_by_field("status", 0)

    def search_by_name(self, keyword: str) -> list[dict]:
        query = f"SELECT * FROM {self.table_name} WHERE first_name LIKE ? OR last_name LIKE ?"
        return self.db.fetch_all(query, (f"%{keyword}%", f"%{keyword}%"))