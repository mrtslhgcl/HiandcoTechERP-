from database.base_repository import BaseRepository

class UserRepository(BaseRepository):
    def __init__(self):
        super().__init__("users")
        self.create_table({
            "ID": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "employee_ID": "INTEGER NOT NULL REFERENCES employees(ID)",
            "username": "TEXT NOT NULL UNIQUE",
            "password_hash": "TEXT NOT NULL",
            "is_active": "INTEGER DEFAULT 1",
            "last_login": "TEXT DEFAULT NULL",
            "created_at": "TEXT NOT NULL"
        })

    def get_by_username(self, username: str) -> dict | None:
        results = self.get_by_field("username", username)
        return results[0] if results else None

    def get_by_employee_id(self, employee_id: int) -> dict | None:
        results = self.get_by_field("employee_ID", employee_id)
        return results[0] if results else None

    def get_active_users(self) -> list[dict]:
        return self.get_by_field("is_active", 1)

    def update_last_login(self, user_id: int, login_time: str) -> bool:
        return self.update(user_id, {"last_login": login_time})