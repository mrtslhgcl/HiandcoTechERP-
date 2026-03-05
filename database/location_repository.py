from database.base_repository import BaseRepository


class LocationRepository(BaseRepository):
    def __init__(self):
        super().__init__("locations")
        self.create_table({
            "ID": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "name": "TEXT NOT NULL",
            "parent_location_ID": "INTEGER DEFAULT NULL",
            "description": "TEXT DEFAULT ''",
            "created_at": "TEXT NOT NULL"
        })

    def get_by_name(self, name: str) -> list[dict]:
        return self.get_by_field("name", name)

    def get_by_parent(self, parent_id) -> list[dict]:
        if parent_id is None:
            query = f"SELECT * FROM {self.table_name} WHERE parent_location_ID IS NULL"
            return self.db.fetch_all(query)
        return self.get_by_field("parent_location_ID", parent_id)

    def get_root_locations(self) -> list[dict]:
        return self.get_by_parent(None)

    def search_by_name(self, keyword: str) -> list[dict]:
        return self.search("name", keyword)

    def get_children_count(self, location_id: int) -> int:
        children = self.get_by_parent(location_id)
        return len(children)

    def get_all_children_ids(self, location_id: int) -> list[int]:
        ids = []
        children = self.get_by_parent(location_id)
        for child in children:
            ids.append(child["ID"])
            ids.extend(self.get_all_children_ids(child["ID"]))
        return ids