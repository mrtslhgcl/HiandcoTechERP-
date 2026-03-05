from datetime import datetime
from database.brand_repository import BrandRepository
from database.product_repository import ProductRepository
from utils.logger import Logger
from utils.session import Session


class BrandController:
    def __init__(self):
        self.brand_repo = BrandRepository()
        self.product_repo = ProductRepository()
        self.logger = Logger()
        self.session = Session()

    def _get_user(self) -> str:
        return self.session.get_log_user()

    def add_brand(self, name: str, description: str = "", logo_path: str = "") -> dict:
        if not self.session.has_permission("brand_create"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok", "brand_id": None}

        existing = self.brand_repo.get_by_name(name)
        if existing:
            return {"success": False, "message": "Bu marka adı zaten mevcut", "brand_id": None}

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        brand_id = self.brand_repo.insert({
            "name": name,
            "description": description,
            "logo_path": logo_path,
            "created_at": now
        })

        self.logger.info(self._get_user(), "BrandController", "Marka eklendi", {
            "brand_id": brand_id,
            "name": name
        })

        return {"success": True, "message": "Marka başarıyla eklendi", "brand_id": brand_id}

    def update_brand(self, brand_id: int, data: dict) -> dict:
        if not self.session.has_permission("brand_update"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        brand = self.brand_repo.get_by_id(brand_id)
        if brand is None:
            return {"success": False, "message": "Marka bulunamadı"}

        if "name" in data and data["name"] != brand["name"]:
            existing = self.brand_repo.get_by_name(data["name"])
            if existing:
                return {"success": False, "message": "Bu marka adı zaten mevcut"}

        self.brand_repo.update(brand_id, data)

        self.logger.info(self._get_user(), "BrandController", "Marka güncellendi", {
            "brand_id": brand_id,
            "updated_fields": list(data.keys())
        })

        return {"success": True, "message": "Marka başarıyla güncellendi"}

    def delete_brand(self, brand_id: int) -> dict:
        if not self.session.has_permission("brand_delete"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        brand = self.brand_repo.get_by_id(brand_id)
        if brand is None:
            return {"success": False, "message": "Marka bulunamadı"}

        products = self.product_repo.get_by_brand(brand_id)
        if products:
            return {"success": False, "message": f"Bu markada {len(products)} ürün var. Önce ürünlerin markasını değiştirin."}

        self.brand_repo.delete(brand_id)

        self.logger.info(self._get_user(), "BrandController", "Marka silindi", {
            "brand_id": brand_id,
            "name": brand["name"]
        })

        return {"success": True, "message": "Marka başarıyla silindi"}

    def get_brand(self, brand_id: int) -> dict:
        brand = self.brand_repo.get_by_id(brand_id)
        if brand is None:
            return {"success": False, "message": "Marka bulunamadı", "data": None}

        return {"success": True, "message": "", "data": brand}

    def get_all_brands(self) -> dict:
        brands = self.brand_repo.get_all()
        return {"success": True, "message": "", "data": brands}

    def search_brands(self, keyword: str) -> dict:
        brands = self.brand_repo.search_by_name(keyword)
        return {"success": True, "message": "", "data": brands}