from database.base_repository import BaseRepository

class EmployeeRoleRepository(BaseRepository):
    def __init__(self):
        super().__init__("employee_roles")
        self.create_table({
            "ID": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "employee_ID": "INTEGER NOT NULL REFERENCES employees(ID)",
            "role_ID": "INTEGER NOT NULL REFERENCES roles(ID)",
            "assigned_at": "TEXT NOT NULL"
        })

    def get_roles_by_employee(self, employee_id: int) -> list[dict]:
        return self.get_by_field("employee_ID", employee_id)

    def get_employees_by_role(self, role_id: int) -> list[dict]:
        return self.get_by_field("role_ID", role_id)

    def assign_role(self, employee_id: int, role_id: int, assigned_at: str) -> int:
        return self.insert({
            "employee_ID": employee_id,
            "role_ID": role_id,
            "assigned_at": assigned_at
        })

    def remove_role(self, employee_id: int, role_id: int) -> bool:
        query = f"DELETE FROM {self.table_name} WHERE employee_ID = ? AND role_ID = ?"
        cursor = self.db.execute(query, (employee_id, role_id))
        return cursor.rowcount > 0