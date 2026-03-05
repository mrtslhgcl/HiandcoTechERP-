import json
from datetime import datetime
from database.product_repository import ProductRepository
from database.variant_repository import VariantRepository
from database.brand_repository import BrandRepository
from database.category_repository import CategoryRepository
from database.supplier_repository import SupplierRepository
from utils.logger import Logger
from utils.session import Session


class ProductController:
    def __init__(self):
        self.product_repo = ProductRepository()
        self.variant_repo = VariantRepository()
        self.brand_repo = BrandRepository()
        self.category_repo = CategoryRepository()
        self.supplier_repo = SupplierRepository()
        self.logger = Logger()
        self.session = Session()

    def _get_user(self) -> str:
        return self.session.get_log_user()


    def add_product(self, name: str, description: str = "", main_category_id: int = None,
                    extra_category_ids: list[int] = None, brand_id: int = None,
                    supplier_id: int = None, sale_unit: str = "ADET") -> dict:

        if not self.session.has_permission("product_create"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok", "product_id": None}

        if main_category_id is not None:
            category = self.category_repo.get_by_id(main_category_id)
            if category is None:
                return {"success": False, "message": "Ana kategori bulunamadı", "product_id": None}

        if extra_category_ids:
            for cid in extra_category_ids:
                cat = self.category_repo.get_by_id(cid)
                if cat is None:
                    return {"success": False, "message": f"Ekstra kategori bulunamadı: ID {cid}", "product_id": None}

        if brand_id is not None:
            brand = self.brand_repo.get_by_id(brand_id)
            if brand is None:
                return {"success": False, "message": "Marka bulunamadı", "product_id": None}

        if supplier_id is not None:
            supplier = self.supplier_repo.get_by_id(supplier_id)
            if supplier is None:
                return {"success": False, "message": "Tedarikçi bulunamadı", "product_id": None}

        if not sale_unit or not sale_unit.strip():
            return {"success": False, "message": "Satış birimi boş bırakılamaz", "product_id": None}

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        product_id = self.product_repo.insert({
            "name": name,
            "description": description,
            "main_category_ID": main_category_id,
            "extra_category_IDs": json.dumps(extra_category_ids or []),
            "brand_ID": brand_id,
            "supplier_ID": supplier_id,
            "sale_unit": sale_unit.strip().upper(),
            "is_active": 1,
            "created_at": now
        })

        self.logger.info(self._get_user(), "ProductController", "Ürün eklendi", {
            "product_id": product_id,
            "name": name
        })

        return {"success": True, "message": "Ürün başarıyla eklendi", "product_id": product_id}

    def update_product(self, product_id: int, data: dict) -> dict:
        if not self.session.has_permission("product_update"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        product = self.product_repo.get_by_id(product_id)
        if product is None:
            return {"success": False, "message": "Ürün bulunamadı"}

        if "main_category_ID" in data and data["main_category_ID"] is not None:
            cat = self.category_repo.get_by_id(data["main_category_ID"])
            if cat is None:
                return {"success": False, "message": "Ana kategori bulunamadı"}

        if "extra_category_IDs" in data:
            if isinstance(data["extra_category_IDs"], list):
                for cid in data["extra_category_IDs"]:
                    cat = self.category_repo.get_by_id(cid)
                    if cat is None:
                        return {"success": False, "message": f"Ekstra kategori bulunamadı: ID {cid}"}
                data["extra_category_IDs"] = json.dumps(data["extra_category_IDs"])

        if "brand_ID" in data and data["brand_ID"] is not None:
            brand = self.brand_repo.get_by_id(data["brand_ID"])
            if brand is None:
                return {"success": False, "message": "Marka bulunamadı"}

        if "supplier_ID" in data and data["supplier_ID"] is not None:
            supplier = self.supplier_repo.get_by_id(data["supplier_ID"])
            if supplier is None:
                return {"success": False, "message": "Tedarikçi bulunamadı"}

        self.product_repo.update(product_id, data)

        self.logger.info(self._get_user(), "ProductController", "Ürün güncellendi", {
            "product_id": product_id,
            "updated_fields": list(data.keys())
        })

        return {"success": True, "message": "Ürün başarıyla güncellendi"}

    def delete_product(self, product_id: int) -> dict:
        if not self.session.has_permission("product_delete"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        product = self.product_repo.get_by_id(product_id)
        if product is None:
            return {"success": False, "message": "Ürün bulunamadı"}

        variants = self.variant_repo.get_by_product(product_id)
        if variants:
            return {"success": False, "message": f"Bu ürünün {len(variants)} varyantı var. Önce varyantları silin."}

        self.variant_repo.delete_images_by_product(product_id)
        self.product_repo.delete(product_id)

        self.logger.info(self._get_user(), "ProductController", "Ürün silindi", {
            "product_id": product_id,
            "name": product["name"]
        })

        return {"success": True, "message": "Ürün başarıyla silindi"}

    def get_product(self, product_id: int) -> dict:
        product = self.product_repo.get_by_id(product_id)
        if product is None:
            return {"success": False, "message": "Ürün bulunamadı", "data": None}

        product["extra_category_IDs"] = json.loads(product.get("extra_category_IDs", "[]"))
        product["variants"] = self.variant_repo.get_by_product_with_attributes(product_id)

        return {"success": True, "message": "", "data": product}

    def get_all_products(self) -> dict:
        products = self.product_repo.get_all()
        return {"success": True, "message": "", "data": products}

    def get_active_products(self) -> dict:
        products = self.product_repo.get_active_products()
        return {"success": True, "message": "", "data": products}

    def search_products(self, keyword: str) -> dict:
        products = self.product_repo.search_by_name(keyword)
        return {"success": True, "message": "", "data": products}

    def get_products_by_brand(self, brand_id: int) -> dict:
        products = self.product_repo.get_by_brand(brand_id)
        return {"success": True, "message": "", "data": products}

    def get_products_by_category(self, category_id: int) -> dict:
        products = self.product_repo.get_by_any_category(category_id)
        return {"success": True, "message": "", "data": products}

    def get_products_by_supplier(self, supplier_id: int) -> dict:
        products = self.product_repo.get_by_supplier(supplier_id)
        return {"success": True, "message": "", "data": products}

    def deactivate_product(self, product_id: int) -> dict:
        if not self.session.has_permission("product_update"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        product = self.product_repo.get_by_id(product_id)
        if product is None:
            return {"success": False, "message": "Ürün bulunamadı"}

        self.product_repo.update(product_id, {"is_active": 0})

        self.logger.info(self._get_user(), "ProductController", "Ürün pasife alındı", {
            "product_id": product_id, "name": product["name"]
        })

        return {"success": True, "message": "Ürün pasife alındı"}

    def activate_product(self, product_id: int) -> dict:
        if not self.session.has_permission("product_update"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        product = self.product_repo.get_by_id(product_id)
        if product is None:
            return {"success": False, "message": "Ürün bulunamadı"}

        self.product_repo.update(product_id, {"is_active": 1})

        self.logger.info(self._get_user(), "ProductController", "Ürün aktife alındı", {
            "product_id": product_id, "name": product["name"]
        })

        return {"success": True, "message": "Ürün aktife alındı"}


    def add_variant(self, product_id: int, sku: str, barcode: str,
                    buy_price: float = 0.0, sell_price: float = 0.0,
                    vat_included: bool = False, vat_rate: float = 0.0,
                    attribute_value_ids: list[int] = None) -> dict:

        if not self.session.has_permission("product_create"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok", "variant_id": None}

        product = self.product_repo.get_by_id(product_id)
        if product is None:
            return {"success": False, "message": "Ürün bulunamadı", "variant_id": None}

        existing_sku = self.variant_repo.get_by_sku(sku)
        if existing_sku:
            return {"success": False, "message": "Bu SKU zaten kullanılıyor", "variant_id": None}

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        variant_id = self.variant_repo.insert({
            "product_ID": product_id,
            "sku": sku,
            "barcode": barcode,
            "buy_price": buy_price,
            "sell_price": sell_price,
            "vat_included": 1 if vat_included else 0,
            "vat_rate": vat_rate,
            "location_quantities": json.dumps({}),
            "created_at": now
        })

        if attribute_value_ids:
            self.variant_repo.add_attributes(variant_id, attribute_value_ids)

        self.logger.info(self._get_user(), "ProductController", "Varyant eklendi", {
            "variant_id": variant_id,
            "product_id": product_id,
            "sku": sku,
            "barcode": barcode,
            "attributes": attribute_value_ids or []
        })

        return {"success": True, "message": "Varyant başarıyla eklendi", "variant_id": variant_id}

    def update_variant(self, variant_id: int, data: dict,
                       attribute_value_ids: list[int] = None) -> dict:

        if not self.session.has_permission("product_update"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        variant = self.variant_repo.get_by_id(variant_id)
        if variant is None:
            return {"success": False, "message": "Varyant bulunamadı"}

        if "sku" in data and data["sku"] != variant["sku"]:
            existing = self.variant_repo.get_by_sku(data["sku"])
            if existing:
                return {"success": False, "message": "Bu SKU zaten kullanılıyor"}

        if "vat_included" in data:
            data["vat_included"] = 1 if data["vat_included"] else 0

        if "location_quantities" in data and isinstance(data["location_quantities"], dict):
            data["location_quantities"] = json.dumps(data["location_quantities"])

        self.variant_repo.update(variant_id, data)

        if attribute_value_ids is not None:
            self.variant_repo.delete_attributes(variant_id)
            self.variant_repo.add_attributes(variant_id, attribute_value_ids)

        self.logger.info(self._get_user(), "ProductController", "Varyant güncellendi", {
            "variant_id": variant_id,
            "updated_fields": list(data.keys())
        })

        return {"success": True, "message": "Varyant başarıyla güncellendi"}

    def delete_variant(self, variant_id: int) -> dict:
        if not self.session.has_permission("product_delete"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        variant = self.variant_repo.get_by_id(variant_id)
        if variant is None:
            return {"success": False, "message": "Varyant bulunamadı"}

        self.variant_repo.delete_images_by_variant(variant_id)
        self.variant_repo.delete_attributes(variant_id)
        self.variant_repo.delete(variant_id)

        self.logger.info(self._get_user(), "ProductController", "Varyant silindi", {
            "variant_id": variant_id,
            "sku": variant["sku"],
            "barcode": variant["barcode"]
        })

        return {"success": True, "message": "Varyant başarıyla silindi"}

    def get_variant(self, variant_id: int) -> dict:
        variant = self.variant_repo.get_variant_with_attributes(variant_id)
        if variant is None:
            return {"success": False, "message": "Varyant bulunamadı", "data": None}

        variant["location_quantities"] = json.loads(variant.get("location_quantities", "{}"))
        variant["total_quantity"] = sum(variant["location_quantities"].values())

        return {"success": True, "message": "", "data": variant}

    def get_variant_by_barcode(self, barcode: str) -> dict:
        variant = self.variant_repo.get_by_barcode(barcode)
        if not variant:
            return {"success": False, "message": "Bu barkoda ait varyant bulunamadı", "data": None}

        variant["attributes"] = self.variant_repo.get_attributes(variant["ID"])
        variant["location_quantities"] = json.loads(variant.get("location_quantities", "{}"))
        variant["total_quantity"] = sum(variant["location_quantities"].values())
        product = self.product_repo.get_by_id(variant["product_ID"])
        variant["product_name"] = product["name"] if product else "Bilinmiyor"

        return {"success": True, "message": "", "data": variant}

    def get_product_variants(self, product_id: int) -> dict:
        variants = self.variant_repo.get_by_product_with_attributes(product_id)
        for v in variants:
            v["location_quantities"] = json.loads(v.get("location_quantities", "{}"))
            v["total_quantity"] = sum(v["location_quantities"].values())

        return {"success": True, "message": "", "data": variants}

    def get_low_stock_variants(self, threshold: int = 10) -> dict:
        variants = self.variant_repo.get_low_stock_variants(threshold)
        return {"success": True, "message": "", "data": variants}
    
    def get_main_category(self, product_id: int) -> dict:
        product = self.product_repo.get_by_id(product_id)
        if product is None:
            return {"success": False, "message": "Ürün bulunamadı", "data": None}
        else:
            pass
                
        category = self.category_repo.get_by_id(product["main_category_ID"])
    
        if category is None:
            return {"success": False, "message": "Ana kategori bulunamadı", "data": None}
        else:
            return {"success": True, "message": "", "data": category}

    def get_variant_attributes(self, variant_id: int) -> dict:
        variant = self.variant_repo.get_by_id(variant_id)
        if variant is None:
            return {"success": False, "message": "Varyant bulunamadı", "data": None}

        attributes = self.variant_repo.get_attributes(variant_id)
        return {"success": True, "message": "", "data": attributes}


    def add_product_image(self, product_id: int, image_path: str, variant_id: int = None, image_data: str = None) -> dict:
        if not self.session.has_permission("product_update"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok", "image_id": None}

        product = self.product_repo.get_by_id(product_id)
        if product is None:
            return {"success": False, "message": "Ürün bulunamadı", "image_id": None}

        if variant_id is not None:
            variant = self.variant_repo.get_by_id(variant_id)
            if variant is None:
                return {"success": False, "message": "Varyant bulunamadı", "image_id": None}
            if variant["product_ID"] != product_id:
                return {"success": False, "message": "Bu varyant bu ürüne ait değil", "image_id": None}

        if not image_path or not image_path.strip():
            return {"success": False, "message": "Resim yolu boş bırakılamaz", "image_id": None}

        image_id = self.variant_repo.add_image(product_id, image_path.strip(), variant_id, image_data)

        self.logger.info(self._get_user(), "ProductController", "Ürün resmi eklendi", {
            "product_id": product_id,
            "variant_id": variant_id,
            "image_path": image_path
        })

        return {"success": True, "message": "Resim başarıyla eklendi", "image_id": image_id}

    def get_product_images(self, product_id: int) -> dict:
        product = self.product_repo.get_by_id(product_id)
        if product is None:
            return {"success": False, "message": "Ürün bulunamadı", "data": None}

        images = self.variant_repo.get_images_by_product(product_id)
        return {"success": True, "message": "", "data": images}

    def get_general_product_images(self, product_id: int) -> dict:
        product = self.product_repo.get_by_id(product_id)
        if product is None:
            return {"success": False, "message": "Ürün bulunamadı", "data": None}

        images = self.variant_repo.get_general_images(product_id)
        return {"success": True, "message": "", "data": images}

    def get_variant_images(self, variant_id: int) -> dict:
        variant = self.variant_repo.get_by_id(variant_id)
        if variant is None:
            return {"success": False, "message": "Varyant bulunamadı", "data": None}

        images = self.variant_repo.get_images_by_variant(variant_id)
        return {"success": True, "message": "", "data": images}

    def delete_product_image(self, image_id: int) -> dict:
        if not self.session.has_permission("product_update"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        image = self.variant_repo.get_image_by_id(image_id)
        if image is None:
            return {"success": False, "message": "Resim bulunamadı"}

        self.variant_repo.delete_image(image_id)

        self.logger.info(self._get_user(), "ProductController", "Ürün resmi silindi", {
            "image_id": image_id,
            "product_id": image["product_ID"],
            "variant_id": image["variant_ID"]
        })

        return {"success": True, "message": "Resim başarıyla silindi"}