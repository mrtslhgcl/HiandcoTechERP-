from database.base_repository import BaseRepository
import json
from datetime import datetime


class RoleRepository(BaseRepository):
    def __init__(self):
        super().__init__("roles")
        self.create_table({
            "ID": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "name": "TEXT NOT NULL UNIQUE",
            "description": "TEXT DEFAULT ''",
            "permission_IDs": "TEXT DEFAULT '[]'",
            "created_at": "TEXT NOT NULL"
        })
        self._seed_admin_role()

    def _seed_admin_role(self):
        from database.permissions_repository import PermissionRepository
        perm_repo = PermissionRepository()
        all_perms = perm_repo.get_all_permissions()
        perm_ids = [p["ID"] for p in all_perms]

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        existing = self.get_by_name("admin")

        if existing is None:
            self.insert({
                "name": "admin",
                "description": "Tüm yetkilere sahip rol",
                "permission_IDs": json.dumps(perm_ids),
                "created_at": now
            })
        else:
            self.update(existing["ID"], {
                "permission_IDs": json.dumps(perm_ids)
            })

    def get_by_name(self, name: str) -> dict | None:
        results = self.get_by_field("name", name)
        return results[0] if results else None