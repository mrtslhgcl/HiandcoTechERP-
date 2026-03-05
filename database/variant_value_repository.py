from database.base_repository import BaseRepository

class VariantValueRepository(BaseRepository):
    def __init__(self):
        super().__init__("variant_values")
        self.create_table({
            "ID": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "variant_type_ID": "INTEGER NOT NULL REFERENCES variant_types(ID)",
            "value": "TEXT NOT NULL",
            "created_at": "TEXT NOT NULL"
        })

    def get_by_type(self, variant_type_id: int) -> list[dict]:
        return self.get_by_field("variant_type_ID", variant_type_id)

    def get_by_type_and_value(self, variant_type_id: int, value: str) -> dict | None:
        query = f"""
            SELECT * FROM {self.table_name} 
            WHERE variant_type_ID = ? AND value = ?
        """
        results = self.db.fetch_all(query, (variant_type_id, value))
        return results[0] if results else None

    def get_values_by_type_name(self, type_name: str) -> list[dict]:
        query = f"""
            SELECT vv.* FROM {self.table_name} vv
            JOIN variant_types vt ON vv.variant_type_ID = vt.ID
            WHERE vt.name = ?
        """
        return self.db.fetch_all(query, (type_name,))

    def delete_by_type(self, variant_type_id: int):
        query = f"DELETE FROM {self.table_name} WHERE variant_type_ID = ?"
        self.db.execute(query, (variant_type_id,))