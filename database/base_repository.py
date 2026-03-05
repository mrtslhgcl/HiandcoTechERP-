from database.database_adapter import DatabaseAdapter


class BaseRepository:
    def __init__(self, table_name: str):
        self.table_name = table_name
        self.db = DatabaseAdapter()

    def create_table(self, columns: dict[str, str]):
        cols = ", ".join([f"{col} {dtype}" for col, dtype in columns.items()])
        query = f"CREATE TABLE IF NOT EXISTS {self.table_name} ({cols})"
        self.db.execute(query)

    def _ensure_column(self, column_name: str, column_def: str, table_name: str = None):
        tbl = table_name or self.table_name
        try:
            self.db.execute(f"ALTER TABLE {tbl} ADD COLUMN {column_name} {column_def}")
        except Exception:
            pass

    def insert(self, data: dict) -> int:
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
        cursor = self.db.execute(query, tuple(data.values()))
        return cursor.lastrowid

    def update(self, id: int, data: dict) -> bool:
        set_clause = ", ".join([f"{col} = ?" for col in data.keys()])
        query = f"UPDATE {self.table_name} SET {set_clause} WHERE ID = ?"
        params = tuple(data.values()) + (id,)
        cursor = self.db.execute(query, params)
        return cursor.rowcount > 0

    def delete(self, id: int) -> bool:
        query = f"DELETE FROM {self.table_name} WHERE ID = ?"
        cursor = self.db.execute(query, (id,))
        return cursor.rowcount > 0

    def get_by_id(self, id: int) -> dict | None:
        query = f"SELECT * FROM {self.table_name} WHERE ID = ?"
        return self.db.fetch_one(query, (id,))

    def get_all(self) -> list[dict]:
        query = f"SELECT * FROM {self.table_name}"
        return self.db.fetch_all(query)

    def get_by_field(self, field: str, value) -> list[dict]:
        query = f"SELECT * FROM {self.table_name} WHERE {field} = ?"
        return self.db.fetch_all(query, (value,))

    def get_by_fields(self, filters: dict) -> list[dict]:
        where_clause = " AND ".join([f"{col} = ?" for col in filters.keys()])
        query = f"SELECT * FROM {self.table_name} WHERE {where_clause}"
        return self.db.fetch_all(query, tuple(filters.values()))

    def count(self, filters: dict = None) -> int:
        if filters:
            where_clause = " AND ".join([f"{col} = ?" for col in filters.keys()])
            query = f"SELECT COUNT(*) as count FROM {self.table_name} WHERE {where_clause}"
            result = self.db.fetch_one(query, tuple(filters.values()))
        else:
            query = f"SELECT COUNT(*) as count FROM {self.table_name}"
            result = self.db.fetch_one(query)
        return result["count"] if result else 0

    def exists(self, filters: dict) -> bool:
        return self.count(filters) > 0

    def search(self, field: str, keyword: str) -> list[dict]:
        query = f"SELECT * FROM {self.table_name} WHERE {field} LIKE ?"
        return self.db.fetch_all(query, (f"%{keyword}%",))

    def get_paginated(self, page: int = 1, per_page: int = 50, order_by: str = "ID", descending: bool = False) -> list[dict]:
        direction = "DESC" if descending else "ASC"
        offset = (page - 1) * per_page
        query = f"SELECT * FROM {self.table_name} ORDER BY {order_by} {direction} LIMIT ? OFFSET ?"
        return self.db.fetch_all(query, (per_page, offset))