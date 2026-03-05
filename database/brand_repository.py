from database.base_repository import BaseRepository

class BrandRepository(BaseRepository):
    def __init__(self):
        super().__init__("brands")
        self.create_table({
            "ID": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "name": "TEXT NOT NULL UNIQUE",
            "description": "TEXT DEFAULT ''",
            "logo_path": "TEXT DEFAULT ''",
            "image_data": "TEXT DEFAULT ''",
            "created_at": "TEXT NOT NULL"
        })
        self._ensure_column("image_data", "TEXT DEFAULT ''")

    def get_by_name(self, name: str) -> dict | None:
        results = self.get_by_field("name", name)
        return results[0] if results else None

    def search_by_name(self, keyword: str) -> list[dict]:
        return self.search("name", keyword)