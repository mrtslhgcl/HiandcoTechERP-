import json
from datetime import datetime
from database.location_repository import LocationRepository
from utils.logger import Logger
from utils.session import Session


class LocationController:
    def __init__(self):
        self.location_repo = LocationRepository()
        self.logger = Logger()
        self.session = Session()

    def _get_user(self) -> str:
        return self.session.get_log_user()

    def add_location(self, name: str, parent_location_ID: int = None,
                     description: str = "") -> dict:

        if not self.session.has_permission("location_create"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok", "location_id": None}

        if not name.strip():
            return {"success": False, "message": "Lokasyon adı boş bırakılamaz", "location_id": None}

        siblings = self.location_repo.get_by_parent(parent_location_ID)
        for s in siblings:
            if s["name"].lower() == name.strip().lower():
                return {"success": False, "message": "Bu lokasyon adı aynı seviyede zaten mevcut", "location_id": None}

        if parent_location_ID is not None:
            parent = self.location_repo.get_by_id(parent_location_ID)
            if parent is None:
                return {"success": False, "message": "Üst lokasyon bulunamadı", "location_id": None}

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        location_id = self.location_repo.insert({
            "name": name.strip(),
            "parent_location_ID": parent_location_ID,
            "description": description,
            "created_at": now
        })

        self.logger.info(self._get_user(), "LocationController", "Lokasyon eklendi", {
            "location_id": location_id,
            "name": name,
            "parent_id": parent_location_ID
        })

        return {"success": True, "message": "Lokasyon başarıyla eklendi", "location_id": location_id}

    def update_location(self, location_id: int, data: dict) -> dict:
        if not self.session.has_permission("location_update"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        location = self.location_repo.get_by_id(location_id)
        if location is None:
            return {"success": False, "message": "Lokasyon bulunamadı"}

        if "name" in data:
            parent_id = data.get("parent_location_ID", location.get("parent_location_ID"))
            siblings = self.location_repo.get_by_parent(parent_id)
            for s in siblings:
                if s["ID"] != location_id and s["name"].lower() == data["name"].strip().lower():
                    return {"success": False, "message": "Bu lokasyon adı aynı seviyede zaten mevcut"}

        if "parent_location_ID" in data and data["parent_location_ID"] is not None:
            if data["parent_location_ID"] == location_id:
                return {"success": False, "message": "Lokasyon kendisinin altına taşınamaz"}

            child_ids = self.location_repo.get_all_children_ids(location_id)
            if data["parent_location_ID"] in child_ids:
                return {"success": False, "message": "Lokasyon kendi alt lokasyonunun altına taşınamaz"}

        self.location_repo.update(location_id, data)

        self.logger.info(self._get_user(), "LocationController", "Lokasyon güncellendi", {
            "location_id": location_id,
            "updated_fields": list(data.keys())
        })

        return {"success": True, "message": "Lokasyon başarıyla güncellendi"}

    def delete_location(self, location_id: int) -> dict:
        if not self.session.has_permission("location_delete"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        location = self.location_repo.get_by_id(location_id)
        if location is None:
            return {"success": False, "message": "Lokasyon bulunamadı"}

        children = self.location_repo.get_by_parent(location_id)
        if children:
            return {"success": False, "message": f"Bu lokasyonun {len(children)} alt lokasyonu var. Önce onları silin."}

        self.location_repo.delete(location_id)

        self.logger.info(self._get_user(), "LocationController", "Lokasyon silindi", {
            "location_id": location_id,
            "name": location["name"]
        })

        return {"success": True, "message": "Lokasyon başarıyla silindi"}

    def get_location(self, location_id: int) -> dict:
        location = self.location_repo.get_by_id(location_id)
        if location is None:
            return {"success": False, "message": "Lokasyon bulunamadı", "data": None}
        return {"success": True, "message": "", "data": location}

    def get_all_locations(self) -> dict:
        locations = self.location_repo.get_all()
        return {"success": True, "message": "", "data": locations}

    def get_root_locations(self) -> dict:
        locations = self.location_repo.get_root_locations()
        return {"success": True, "message": "", "data": locations}

    def get_children(self, location_id: int) -> dict:
        children = self.location_repo.get_by_parent(location_id)
        return {"success": True, "message": "", "data": children}

    def get_location_tree(self) -> list[dict]:
        all_locations = self.location_repo.get_all()

        def build_tree(parent_id=None):
            nodes = []
            for loc in all_locations:
                if loc.get("parent_location_ID") == parent_id:
                    node = dict(loc)
                    node["children"] = build_tree(loc["ID"])
                    nodes.append(node)
            return nodes

        return build_tree()