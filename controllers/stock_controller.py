import json
from datetime import datetime
from database.variant_repository import VariantRepository
from database.stock_movement_repository import StockMovementRepository
from database.location_repository import LocationRepository
from utils.logger import Logger
from utils.session import Session

class StockController:
    def __init__(self):
        self.variant_repo = VariantRepository()
        self.movement_repo = StockMovementRepository()
        self.location_repo = LocationRepository()
        self.logger = Logger()
        self.session = Session()

    def _get_user(self) -> str:
        return self.session.get_log_user()

    def _get_location_quantities(self, variant_id: int) -> dict:
        variant = self.variant_repo.get_by_id(variant_id)
        if variant is None:
            return {}
        return json.loads(variant.get("location_quantities", "{}"))

    def _save_location_quantities(self, variant_id: int, quantities: dict):
        self.variant_repo.update(variant_id, {
            "location_quantities": json.dumps(quantities)
        })

    def stock_in(self, variant_id: int, location_id: int, quantity: int,
                 reason: str = "", reference_id: int = None) -> dict:

        if not self.session.has_permission("stock_manage"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        if quantity <= 0:
            return {"success": False, "message": "Miktar 0'dan büyük olmalıdır"}

        variant = self.variant_repo.get_by_id(variant_id)
        if variant is None:
            return {"success": False, "message": "Varyant bulunamadı"}

        location = self.location_repo.get_by_id(location_id)
        if location is None:
            return {"success": False, "message": "Lokasyon bulunamadı"}

        quantities = self._get_location_quantities(variant_id)
        loc_key = str(location_id)
        quantities[loc_key] = quantities.get(loc_key, 0) + quantity
        self._save_location_quantities(variant_id, quantities)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        movement_id = self.movement_repo.insert({
            "variant_ID": variant_id,
            "movement_type": "IN",
            "quantity": quantity,
            "source_location_ID": None,
            "destination_location_ID": location_id,
            "reason": reason,
            "reference_ID": reference_id,
            "created_at": now
        })

        self.logger.info(self._get_user(), "StockController", "Stok girişi yapıldı", {
            "movement_id": movement_id,
            "variant_id": variant_id,
            "sku": variant["sku"],
            "location_id": location_id,
            "location_name": location["name"],
            "quantity": quantity,
            "new_total": quantities[loc_key]
        })

        return {"success": True, "message": f"{quantity} adet stok girişi yapıldı", "movement_id": movement_id}

    def stock_out(self, variant_id: int, location_id: int, quantity: int,
                  reason: str = "", reference_id: int = None) -> dict:

        if not self.session.has_permission("stock_manage"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        if quantity <= 0:
            return {"success": False, "message": "Miktar 0'dan büyük olmalıdır"}

        variant = self.variant_repo.get_by_id(variant_id)
        if variant is None:
            return {"success": False, "message": "Varyant bulunamadı"}

        location = self.location_repo.get_by_id(location_id)
        if location is None:
            return {"success": False, "message": "Lokasyon bulunamadı"}

        quantities = self._get_location_quantities(variant_id)
        loc_key = str(location_id)
        current = quantities.get(loc_key, 0)

        if current < quantity:
            return {"success": False, "message": f"Yetersiz stok. Mevcut: {current}, İstenen: {quantity}"}

        quantities[loc_key] = current - quantity
        if quantities[loc_key] == 0:
            del quantities[loc_key]
        self._save_location_quantities(variant_id, quantities)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        movement_id = self.movement_repo.insert({
            "variant_ID": variant_id,
            "movement_type": "OUT",
            "quantity": quantity,
            "source_location_ID": location_id,
            "destination_location_ID": None,
            "reason": reason,
            "reference_ID": reference_id,
            "created_at": now
        })

        self.logger.info(self._get_user(), "StockController", "Stok çıkışı yapıldı", {
            "movement_id": movement_id,
            "variant_id": variant_id,
            "sku": variant["sku"],
            "location_id": location_id,
            "location_name": location["name"],
            "quantity": quantity,
            "remaining": quantities.get(loc_key, 0)
        })

        return {"success": True, "message": f"{quantity} adet stok çıkışı yapıldı", "movement_id": movement_id}

    def stock_transfer(self, variant_id: int, source_location_id: int,
                       destination_location_id: int, quantity: int,
                       reason: str = "") -> dict:

        if not self.session.has_permission("stock_manage"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        if quantity <= 0:
            return {"success": False, "message": "Miktar 0'dan büyük olmalıdır"}

        if source_location_id == destination_location_id:
            return {"success": False, "message": "Kaynak ve hedef lokasyon aynı olamaz"}

        variant = self.variant_repo.get_by_id(variant_id)
        if variant is None:
            return {"success": False, "message": "Varyant bulunamadı"}

        source_loc = self.location_repo.get_by_id(source_location_id)
        if source_loc is None:
            return {"success": False, "message": "Kaynak lokasyon bulunamadı"}

        dest_loc = self.location_repo.get_by_id(destination_location_id)
        if dest_loc is None:
            return {"success": False, "message": "Hedef lokasyon bulunamadı"}

        quantities = self._get_location_quantities(variant_id)
        source_key = str(source_location_id)
        dest_key = str(destination_location_id)
        current = quantities.get(source_key, 0)

        if current < quantity:
            return {"success": False, "message": f"Yetersiz stok. Mevcut: {current}, İstenen: {quantity}"}

        quantities[source_key] = current - quantity
        if quantities[source_key] == 0:
            del quantities[source_key]
        quantities[dest_key] = quantities.get(dest_key, 0) + quantity
        self._save_location_quantities(variant_id, quantities)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        movement_id = self.movement_repo.insert({
            "variant_ID": variant_id,
            "movement_type": "TRANSFER",
            "quantity": quantity,
            "source_location_ID": source_location_id,
            "destination_location_ID": destination_location_id,
            "reason": reason,
            "reference_ID": None,
            "created_at": now
        })

        self.logger.info(self._get_user(), "StockController", "Stok transferi yapıldı", {
            "movement_id": movement_id,
            "variant_id": variant_id,
            "sku": variant["sku"],
            "from": source_loc["name"],
            "to": dest_loc["name"],
            "quantity": quantity
        })

        return {"success": True, "message": f"{quantity} adet transfer edildi", "movement_id": movement_id}

    def stock_adjustment(self, variant_id: int, location_id: int,
                         new_quantity: int, reason: str = "Sayım düzeltmesi") -> dict:

        if not self.session.has_permission("stock_adjust"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        if new_quantity < 0:
            return {"success": False, "message": "Miktar negatif olamaz"}

        variant = self.variant_repo.get_by_id(variant_id)
        if variant is None:
            return {"success": False, "message": "Varyant bulunamadı"}

        location = self.location_repo.get_by_id(location_id)
        if location is None:
            return {"success": False, "message": "Lokasyon bulunamadı"}

        quantities = self._get_location_quantities(variant_id)
        loc_key = str(location_id)
        old_quantity = quantities.get(loc_key, 0)
        difference = new_quantity - old_quantity

        if difference == 0:
            return {"success": False, "message": "Yeni miktar mevcut miktarla aynı"}

        if new_quantity == 0:
            quantities.pop(loc_key, None)
        else:
            quantities[loc_key] = new_quantity
        self._save_location_quantities(variant_id, quantities)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        movement_type = "ADJUSTMENT_IN" if difference > 0 else "ADJUSTMENT_OUT"
        movement_id = self.movement_repo.insert({
            "variant_ID": variant_id,
            "movement_type": movement_type,
            "quantity": abs(difference),
            "source_location_ID": location_id if difference < 0 else None,
            "destination_location_ID": location_id if difference > 0 else None,
            "reason": reason,
            "reference_ID": None,
            "created_at": now
        })

        self.logger.info(self._get_user(), "StockController", "Stok düzeltmesi yapıldı", {
            "movement_id": movement_id,
            "variant_id": variant_id,
            "sku": variant["sku"],
            "location_id": location_id,
            "location_name": location["name"],
            "old_quantity": old_quantity,
            "new_quantity": new_quantity,
            "difference": difference
        })

        return {"success": True, "message": f"Stok düzeltildi. Eski: {old_quantity}, Yeni: {new_quantity}", "movement_id": movement_id}

    def get_variant_stock(self, variant_id: int) -> dict:
        variant = self.variant_repo.get_by_id(variant_id)
        if variant is None:
            return {"success": False, "message": "Varyant bulunamadı", "data": None}

        quantities = self._get_location_quantities(variant_id)

        stock_detail = []
        for loc_id, qty in quantities.items():
            location = self.location_repo.get_by_id(int(loc_id))
            stock_detail.append({
                "location_id": int(loc_id),
                "location_name": location["name"] if location else "Bilinmiyor",
                "quantity": qty
            })

        total = sum(quantities.values())

        return {
            "success": True,
            "message": "",
            "data": {
                "variant_id": variant_id,
                "sku": variant["sku"],
                "barcode": variant["barcode"],
                "locations": stock_detail,
                "total_quantity": total
            }
        }

    def get_location_stock(self, location_id: int) -> dict:
        location = self.location_repo.get_by_id(location_id)
        if location is None:
            return {"success": False, "message": "Lokasyon bulunamadı", "data": None}

        all_variants = self.variant_repo.get_all()
        loc_key = str(location_id)
        stock_list = []

        for variant in all_variants:
            quantities = json.loads(variant.get("location_quantities", "{}"))
            qty = quantities.get(loc_key, 0)
            if qty > 0:
                stock_list.append({
                    "variant_id": variant["ID"],
                    "sku": variant["sku"],
                    "barcode": variant["barcode"],
                    "quantity": qty
                })

        return {
            "success": True,
            "message": "",
            "data": {
                "location_id": location_id,
                "location_name": location["name"],
                "variants": stock_list,
                "total_variants": len(stock_list)
            }
        }

    def get_stock_movements(self, variant_id: int) -> dict:
        variant = self.variant_repo.get_by_id(variant_id)
        if variant is None:
            return {"success": False, "message": "Varyant bulunamadı", "data": None}

        movements = self.movement_repo.get_by_variant(variant_id)
        return {"success": True, "message": "", "data": movements}

    def get_movements_by_date(self, start_date: str, end_date: str) -> dict:
        movements = self.movement_repo.get_by_date_range(start_date, end_date)
        return {"success": True, "message": "", "data": movements}

    def get_movements_by_location(self, location_id: int) -> dict:
        location = self.location_repo.get_by_id(location_id)
        if location is None:
            return {"success": False, "message": "Lokasyon bulunamadı", "data": None}

        movements = self.movement_repo.get_by_location(location_id)
        return {"success": True, "message": "", "data": movements}

    def get_total_stock_by_product(self, product_id: int) -> dict:
        variants = self.variant_repo.get_by_product(product_id)
        if not variants:
            return {"success": True, "data": 0}

        total = 0
        for variant in variants:
            quantities = self._get_location_quantities(variant["ID"])
            total += sum(quantities.values())

        return {"success": True, "data": total}