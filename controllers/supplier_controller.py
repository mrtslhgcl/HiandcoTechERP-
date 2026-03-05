from datetime import datetime
from database.supplier_repository import SupplierRepository
from database.product_repository import ProductRepository
from utils.logger import Logger
from utils.session import Session


class SupplierController:
    def __init__(self):
        self.supplier_repo = SupplierRepository()
        self.product_repo = ProductRepository()
        self.logger = Logger()
        self.session = Session()

    def _get_user(self) -> str:
        return self.session.get_log_user()

    def add_supplier(self, name: str, description: str = "", email: str = "",
                     phone: str = "", address: str = "", authorized_person: str = "",
                     IBAN: str = "", logo: str = "") -> dict:

        if not self.session.has_permission("supplier_create"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok", "supplier_id": None}

        existing = self.supplier_repo.get_by_name(name)
        if existing:
            return {"success": False, "message": "Bu tedarikçi adı zaten mevcut", "supplier_id": None}

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        supplier_id = self.supplier_repo.insert({
            "name": name,
            "description": description,
            "email": email,
            "phone": phone,
            "address": address,
            "authorized_person": authorized_person,
            "IBAN": IBAN,
            "logo": logo,
            "is_active": 1,
            "created_at": now
        })

        self.logger.info(self._get_user(), "SupplierController", "Tedarikçi eklendi", {
            "supplier_id": supplier_id,
            "name": name
        })

        return {"success": True, "message": "Tedarikçi başarıyla eklendi", "supplier_id": supplier_id}

    def update_supplier(self, supplier_id: int, data: dict) -> dict:
        if not self.session.has_permission("supplier_update"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        supplier = self.supplier_repo.get_by_id(supplier_id)
        if supplier is None:
            return {"success": False, "message": "Tedarikçi bulunamadı"}

        if "name" in data and data["name"] != supplier["name"]:
            existing = self.supplier_repo.get_by_name(data["name"])
            if existing:
                return {"success": False, "message": "Bu tedarikçi adı zaten mevcut"}

        self.supplier_repo.update(supplier_id, data)

        self.logger.info(self._get_user(), "SupplierController", "Tedarikçi güncellendi", {
            "supplier_id": supplier_id,
            "updated_fields": list(data.keys())
        })

        return {"success": True, "message": "Tedarikçi başarıyla güncellendi"}

    def delete_supplier(self, supplier_id: int) -> dict:
        if not self.session.has_permission("supplier_delete"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        supplier = self.supplier_repo.get_by_id(supplier_id)
        if supplier is None:
            return {"success": False, "message": "Tedarikçi bulunamadı"}

        products = self.product_repo.get_by_supplier(supplier_id)
        if products:
            return {"success": False, "message": f"Bu tedarikçiye bağlı {len(products)} ürün var. Silme yerine pasife alın."}

        self.supplier_repo.delete(supplier_id)

        self.logger.info(self._get_user(), "SupplierController", "Tedarikçi silindi", {
            "supplier_id": supplier_id,
            "name": supplier["name"]
        })

        return {"success": True, "message": "Tedarikçi başarıyla silindi"}

    def deactivate_supplier(self, supplier_id: int) -> dict:
        if not self.session.has_permission("supplier_update"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        supplier = self.supplier_repo.get_by_id(supplier_id)
        if supplier is None:
            return {"success": False, "message": "Tedarikçi bulunamadı"}

        self.supplier_repo.update(supplier_id, {"is_active": 0})

        self.logger.info(self._get_user(), "SupplierController", "Tedarikçi pasife alındı", {
            "supplier_id": supplier_id,
            "name": supplier["name"]
        })

        return {"success": True, "message": "Tedarikçi pasife alındı"}

    def activate_supplier(self, supplier_id: int) -> dict:
        if not self.session.has_permission("supplier_update"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        supplier = self.supplier_repo.get_by_id(supplier_id)
        if supplier is None:
            return {"success": False, "message": "Tedarikçi bulunamadı"}

        self.supplier_repo.update(supplier_id, {"is_active": 1})

        self.logger.info(self._get_user(), "SupplierController", "Tedarikçi aktife alındı", {
            "supplier_id": supplier_id,
            "name": supplier["name"]
        })

        return {"success": True, "message": "Tedarikçi aktife alındı"}

    def get_supplier(self, supplier_id: int) -> dict:
        supplier = self.supplier_repo.get_by_id(supplier_id)
        if supplier is None:
            return {"success": False, "message": "Tedarikçi bulunamadı", "data": None}

        return {"success": True, "message": "", "data": supplier}

    def get_all_suppliers(self) -> dict:
        suppliers = self.supplier_repo.get_all()
        return {"success": True, "message": "", "data": suppliers}

    def get_active_suppliers(self) -> dict:
        suppliers = self.supplier_repo.get_active_suppliers()
        return {"success": True, "message": "", "data": suppliers}

    def search_suppliers(self, keyword: str) -> dict:
        suppliers = self.supplier_repo.search_by_name(keyword)
        return {"success": True, "message": "", "data": suppliers}

    def get_supplier_products(self, supplier_id: int) -> dict:
        supplier = self.supplier_repo.get_by_id(supplier_id)
        if supplier is None:
            return {"success": False, "message": "Tedarikçi bulunamadı", "data": None}

        products = self.product_repo.get_by_supplier(supplier_id)
        return {"success": True, "message": "", "data": products}