from database.base_repository import BaseRepository

class CategoryRepository(BaseRepository):
    def __init__(self):
        super().__init__("categories")
        self.create_table({
            "ID": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "name": "TEXT NOT NULL",
            "description": "TEXT DEFAULT ''",
            "parent_category_ID": "INTEGER DEFAULT NULL REFERENCES categories(ID)",
            "created_at": "TEXT NOT NULL"
        })

    def get_by_name(self, name: str) -> list[dict]:
        return self.get_by_field("name", name)

    def get_children(self, parent_id: int) -> list[dict]:
        return self.get_by_field("parent_category_ID", parent_id)

    def get_root_categories(self) -> list[dict]:
        query = f"SELECT * FROM {self.table_name} WHERE parent_category_ID IS NULL"
        return self.db.fetch_all(query)

    def get_ancestors(self, category_id: int) -> list[dict]:
        ancestors = []
        current_id = category_id
        while current_id is not None:
            category = self.get_by_id(current_id)
            if category is None:
                break
            ancestors.append(category)
            current_id = category["parent_category_ID"]
        return ancestors

    def search_by_name(self, keyword: str) -> list[dict]:
        return self.search("name", keyword)