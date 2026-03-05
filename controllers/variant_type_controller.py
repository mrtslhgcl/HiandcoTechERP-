from datetime import datetime
from database.variant_type_repository import VariantTypeRepository
from database.variant_value_repository import VariantValueRepository
from database.variant_repository import VariantRepository
from utils.logger import Logger
from utils.session import Session


class VariantTypeController:
    def __init__(self):
        self.type_repo = VariantTypeRepository()
        self.value_repo = VariantValueRepository()
        self.variant_repo = VariantRepository()
        self.logger = Logger()
        self.session = Session()

    def _get_user(self) -> str:
        return self.session.get_log_user()


    def add_variant_type(self, name: str) -> dict:
        if not self.session.has_permission("variant_type_create"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok", "type_id": None}

        if not name.strip():
            return {"success": False, "message": "Varyant tipi adı boş bırakılamaz", "type_id": None}

        existing = self.type_repo.get_by_name(name.strip())
        if existing:
            return {"success": False, "message": "Bu varyant tipi zaten mevcut", "type_id": None}

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        type_id = self.type_repo.insert({
            "name": name.strip(),
            "created_at": now
        })

        self.logger.info(self._get_user(), "VariantTypeController", "Varyant tipi eklendi", {
            "type_id": type_id,
            "name": name
        })

        return {"success": True, "message": "Varyant tipi başarıyla eklendi", "type_id": type_id}

    def update_variant_type(self, type_id: int, data: dict) -> dict:
        if not self.session.has_permission("variant_type_update"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        variant_type = self.type_repo.get_by_id(type_id)
        if variant_type is None:
            return {"success": False, "message": "Varyant tipi bulunamadı"}

        if "name" in data and data["name"].strip() != variant_type["name"]:
            existing = self.type_repo.get_by_name(data["name"].strip())
            if existing:
                return {"success": False, "message": "Bu varyant tipi adı zaten mevcut"}
            data["name"] = data["name"].strip()

        self.type_repo.update(type_id, data)

        self.logger.info(self._get_user(), "VariantTypeController", "Varyant tipi güncellendi", {
            "type_id": type_id,
            "updated_fields": list(data.keys())
        })

        return {"success": True, "message": "Varyant tipi başarıyla güncellendi"}

    def delete_variant_type(self, type_id: int) -> dict:
        if not self.session.has_permission("variant_type_delete"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        variant_type = self.type_repo.get_by_id(type_id)
        if variant_type is None:
            return {"success": False, "message": "Varyant tipi bulunamadı"}

        values = self.value_repo.get_by_type(type_id)
        if values:
            return {"success": False, "message": f"Bu tipe ait {len(values)} değer var. Önce değerleri silin."}

        self.type_repo.delete(type_id)

        self.logger.info(self._get_user(), "VariantTypeController", "Varyant tipi silindi", {
            "type_id": type_id,
            "name": variant_type["name"]
        })

        return {"success": True, "message": "Varyant tipi başarıyla silindi"}

    def get_all_types(self) -> dict:
        types = self.type_repo.get_all()
        return {"success": True, "message": "", "data": types}

    def get_type_with_values(self, type_id: int) -> dict:
        variant_type = self.type_repo.get_by_id(type_id)
        if variant_type is None:
            return {"success": False, "message": "Varyant tipi bulunamadı", "data": None}

        variant_type["values"] = self.value_repo.get_by_type(type_id)
        return {"success": True, "message": "", "data": variant_type}

    def get_all_types_with_values(self) -> dict:
        types = self.type_repo.get_all()
        for t in types:
            t["values"] = self.value_repo.get_by_type(t["ID"])
        return {"success": True, "message": "", "data": types}


    def add_variant_value(self, type_id: int, value: str) -> dict:
        if not self.session.has_permission("variant_type_create"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok", "value_id": None}

        if not value.strip():
            return {"success": False, "message": "Değer boş bırakılamaz", "value_id": None}

        variant_type = self.type_repo.get_by_id(type_id)
        if variant_type is None:
            return {"success": False, "message": "Varyant tipi bulunamadı", "value_id": None}

        existing = self.value_repo.get_by_type_and_value(type_id, value.strip())
        if existing:
            return {"success": False, "message": "Bu değer zaten mevcut", "value_id": None}

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        value_id = self.value_repo.insert({
            "variant_type_ID": type_id,
            "value": value.strip(),
            "created_at": now
        })

        self.logger.info(self._get_user(), "VariantTypeController", "Varyant değeri eklendi", {
            "value_id": value_id,
            "type_id": type_id,
            "value": value
        })

        return {"success": True, "message": "Değer başarıyla eklendi", "value_id": value_id}

    def update_variant_value(self, value_id: int, new_value: str) -> dict:
        if not self.session.has_permission("variant_type_update"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        variant_value = self.value_repo.get_by_id(value_id)
        if variant_value is None:
            return {"success": False, "message": "Değer bulunamadı"}

        if not new_value.strip():
            return {"success": False, "message": "Değer boş bırakılamaz"}

        existing = self.value_repo.get_by_type_and_value(
            variant_value["variant_type_ID"], new_value.strip()
        )
        if existing and existing["ID"] != value_id:
            return {"success": False, "message": "Bu değer zaten mevcut"}

        self.value_repo.update(value_id, {"value": new_value.strip()})

        self.logger.info(self._get_user(), "VariantTypeController", "Varyant değeri güncellendi", {
            "value_id": value_id,
            "new_value": new_value
        })

        return {"success": True, "message": "Değer başarıyla güncellendi"}

    def delete_variant_value(self, value_id: int) -> dict:
        if not self.session.has_permission("variant_type_delete"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        variant_value = self.value_repo.get_by_id(value_id)
        if variant_value is None:
            return {"success": False, "message": "Değer bulunamadı"}

        query = """
            SELECT COUNT(*) as count FROM variant_attributes 
            WHERE variant_value_ID = ?
        """
        result = self.variant_repo.db.fetch_all(query, (value_id,))
        count = result[0]["count"] if result else 0

        if count > 0:
            return {"success": False, "message": f"Bu değer {count} varyant tarafından kullanılıyor. Silinemez."}

        self.value_repo.delete(value_id)

        self.logger.info(self._get_user(), "VariantTypeController", "Varyant değeri silindi", {
            "value_id": value_id,
            "value": variant_value["value"]
        })

        return {"success": True, "message": "Değer başarıyla silindi"}

    def get_values_by_type(self, type_id: int) -> dict:
        values = self.value_repo.get_by_type(type_id)
        return {"success": True, "message": "", "data": values}
    
    def get_items_by_variant_value(self, value_id: int) -> dict:
        query = """
            SELECT v.*, p.name as product_name FROM variants v
            JOIN products p ON v.product_ID = p.ID
            JOIN variant_attributes va ON va.variant_ID = v.ID
            WHERE va.variant_value_ID = ?
        """
        items = self.variant_repo.db.fetch_all(query, (value_id,))
        return {"success": True, "message": "", "data": items}