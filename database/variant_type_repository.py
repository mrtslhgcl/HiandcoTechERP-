from database.base_repository import BaseRepository

class VariantTypeRepository(BaseRepository):
    def __init__(self):
        super().__init__("variant_types")
        self.create_table({
            "ID": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "name": "TEXT NOT NULL UNIQUE",
            "created_at": "TEXT NOT NULL"
        })

    def get_by_name(self, name: str) -> list[dict]:
        return self.get_by_field("name", name)

    def get_all_names(self) -> list[str]:
        results = self.get_all()
        return [r["name"] for r in results]