from database.base_repository import BaseRepository


class StockMovementRepository(BaseRepository):
    def __init__(self):
        super().__init__("stock_movements")
        self.create_table({
            "ID": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "variant_ID": "INTEGER NOT NULL REFERENCES variants(ID)",
            "movement_type": "TEXT NOT NULL",
            "quantity": "INTEGER NOT NULL",
            "source_location_ID": "INTEGER DEFAULT NULL REFERENCES locations(ID)",
            "destination_location_ID": "INTEGER DEFAULT NULL REFERENCES locations(ID)",
            "reason": "TEXT DEFAULT ''",
            "reference_ID": "INTEGER DEFAULT NULL",
            "created_at": "TEXT NOT NULL"
        })

    def get_by_variant(self, variant_id: int) -> list[dict]:
        return self.get_by_field("variant_ID", variant_id)

    def get_by_type(self, movement_type: str) -> list[dict]:
        return self.get_by_field("movement_type", movement_type)

    def get_by_location(self, location_id: int) -> list[dict]:
        query = f"""
            SELECT * FROM {self.table_name} 
            WHERE source_location_ID = ? OR destination_location_ID = ?
        """
        return self.db.fetch_all(query, (location_id, location_id))

    def get_by_date_range(self, start_date: str, end_date: str) -> list[dict]:
        query = f"""
            SELECT * FROM {self.table_name} 
            WHERE created_at BETWEEN ? AND ?
            ORDER BY created_at DESC
        """
        return self.db.fetch_all(query, (start_date, end_date))

    def get_by_variant_and_type(self, variant_id: int, movement_type: str) -> list[dict]:
        return self.get_by_fields({
            "variant_ID": variant_id,
            "movement_type": movement_type
        })