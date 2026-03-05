import json
from datetime import datetime
from database.order_repository import OrderRepository
from database.order_item_repository import OrderItemRepository
from database.payment_repository import PaymentRepository
from database.customer_repository import CustomerRepository
from database.variant_repository import VariantRepository
from database.product_repository import ProductRepository
from controllers.stock_controller import StockController
from utils.logger import Logger
from utils.session import Session

class OrderController:
    def __init__(self):
        self.order_repo = OrderRepository()
        self.order_item_repo = OrderItemRepository()
        self.payment_repo = PaymentRepository()
        self.customer_repo = CustomerRepository()
        self.variant_repo = VariantRepository()
        self.product_repo = ProductRepository()
        self.stock_controller = StockController()
        self.logger = Logger()
        self.session = Session()

    def _get_user(self) -> str:
        return self.session.get_log_user()

    def create_order(self, items: list[dict], customer_id: int = 0,
                     location_id: int = None, currency: str = "TRY",
                     shipping_address: str = "In-store Pickup",
                     billing_address: str = "In-store Pickup",
                     notes: str = "", is_gift: bool = False,
                     gift_message: str = "", discount_code: str = "",
                     discount_price: float = 0.0) -> dict:
        
        if not self.session.has_permission("order_create"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok", "order_id": None}

        if not items:
            return {"success": False, "message": "Sipariş en az bir ürün içermelidir", "order_id": None}

        if customer_id > 0:
            customer = self.customer_repo.get_by_id(customer_id)
            if customer is None:
                return {"success": False, "message": "Müşteri bulunamadı", "order_id": None}

        validated_items = []
        for item in items:
            variant = self.variant_repo.get_by_id(item["variant_id"])
            if variant is None:
                return {"success": False, "message": f"Varyant bulunamadı: ID {item['variant_id']}", "order_id": None}

            product = self.product_repo.get_by_id(variant["product_ID"])
            if product is None:
                return {"success": False, "message": f"Ürün bulunamadı: Varyant ID {item['variant_id']}", "order_id": None}

            quantities = json.loads(variant.get("location_quantities", "{}"))
            if location_id is not None:
                loc_key = str(location_id)
                available = quantities.get(loc_key, 0)
                if available < item["quantity"]:
                    return {
                        "success": False,
                        "message": f"Yetersiz stok: {product['name']} (SKU: {variant['sku']}) - Mevcut: {available}, İstenen: {item['quantity']}",
                        "order_id": None
                    }
            else:
                total_available = sum(quantities.values())
                if total_available < item["quantity"]:
                    return {
                        "success": False,
                        "message": f"Yetersiz stok: {product['name']} (SKU: {variant['sku']}) - Toplam mevcut: {int(total_available)}, İstenen: {item['quantity']}",
                        "order_id": None
                    }

            validated_items.append({
                "variant": variant,
                "product": product,
                "quantity": item["quantity"],
                "unit_price": item.get("unit_price", variant["sell_price"])
            })

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        order_id = self.order_repo.insert({
            "customer_ID": customer_id,
            "currency": currency,
            "created_at": now,
            "shipping_address": shipping_address,
            "billing_address": billing_address,
            "status": "pending",
            "notes": notes,
            "is_gift": 1 if is_gift else 0,
            "gift_message": gift_message,
            "discount_code": discount_code,
            "discount_price": discount_price
        })

        total_amount = 0.0
        for vi in validated_items:
            self.order_item_repo.insert({
                "order_ID": order_id,
                "product_ID": vi["product"]["ID"],
                "variant_ID": vi["variant"]["ID"],
                "quantity": vi["quantity"],
                "unit_price": vi["unit_price"],
                "product_name": vi["product"]["name"]
            })

            total_amount += vi["quantity"] * vi["unit_price"]

            if location_id is not None:
                self.stock_controller.stock_out(
                    variant_id=vi["variant"]["ID"],
                    location_id=location_id,
                    quantity=vi["quantity"],
                    reason=f"Sipariş #{order_id}",
                    reference_id=order_id
                )
            else:
                remaining_qty = vi["quantity"]
                loc_qtys = json.loads(vi["variant"].get("location_quantities", "{}"))
                for loc_str, loc_qty in sorted(loc_qtys.items(), key=lambda x: -x[1]):
                    if remaining_qty <= 0:
                        break
                    deduct = min(remaining_qty, int(loc_qty))
                    if deduct > 0:
                        self.stock_controller.stock_out(
                            variant_id=vi["variant"]["ID"],
                            location_id=int(loc_str),
                            quantity=deduct,
                            reason=f"Sipariş #{order_id}",
                            reference_id=order_id
                        )
                        remaining_qty -= deduct

        self.logger.info(self._get_user(), "OrderController", "Sipariş oluşturuldu", {
            "order_id": order_id,
            "customer_id": customer_id,
            "item_count": len(validated_items),
            "total_amount": total_amount
        })

        return {
            "success": True,
            "message": "Sipariş başarıyla oluşturuldu",
            "order_id": order_id,
            "total_amount": total_amount
        }

    def update_order_status(self, order_id: int, status: str) -> dict:
        if not self.session.has_permission("order_update"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        valid_statuses = ["pending", "confirmed", "preparing", "shipped", "delivered", "completed", "cancelled"]
        if status not in valid_statuses:
            return {"success": False, "message": f"Geçersiz durum. Geçerli durumlar: {', '.join(valid_statuses)}"}

        order = self.order_repo.get_by_id(order_id)
        if order is None:
            return {"success": False, "message": "Sipariş bulunamadı"}

        if order["status"] == "cancelled":
            return {"success": False, "message": "İptal edilmiş sipariş güncellenemez"}

        old_status = order["status"]
        self.order_repo.update_status(order_id, status)

        self.logger.info(self._get_user(), "OrderController", "Sipariş durumu güncellendi", {
            "order_id": order_id,
            "old_status": old_status,
            "new_status": status
        })

        return {"success": True, "message": f"Sipariş durumu '{status}' olarak güncellendi"}

    def cancel_order(self, order_id: int, reason: str = "",
                     location_id: int = None) -> dict:

        if not self.session.has_permission("order_cancel"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        order = self.order_repo.get_by_id(order_id)
        if order is None:
            return {"success": False, "message": "Sipariş bulunamadı"}

        if order["status"] == "cancelled":
            return {"success": False, "message": "Sipariş zaten iptal edilmiş"}

        if order["status"] == "delivered" or order["status"] == "completed":
            return {"success": False, "message": "Teslim edilmiş veya tamamlanmış sipariş iptal edilemez. İade işlemi yapın."}

        if location_id is not None:
            order_items = self.order_item_repo.get_by_order(order_id)
            for item in order_items:
                self.stock_controller.stock_in(
                    variant_id=item["variant_ID"],
                    location_id=location_id,
                    quantity=item["quantity"],
                    reason=f"Sipariş iptali #{order_id}",
                    reference_id=order_id
                )

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.order_repo.update(order_id, {
            "status": "cancelled",
            "cancellation_reason": reason,
            "cancellation_date": now
        })

        self.logger.info(self._get_user(), "OrderController", "Sipariş iptal edildi", {
            "order_id": order_id,
            "reason": reason
        })

        return {"success": True, "message": "Sipariş iptal edildi"}

    def refund_order(self, order_id: int, refund_price: float, reason: str = "",
                     location_id: int = None, refund_items: list[dict] = None) -> dict:
        if not self.session.has_permission("order_refund"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        order = self.order_repo.get_by_id(order_id)
        if order is None:
            return {"success": False, "message": "Sipariş bulunamadı"}

        if order["status"] == "cancelled":
            return {"success": False, "message": "İptal edilmiş siparişe iade yapılamaz"}

        order_total = self.order_item_repo.get_order_total(order_id)
        discount = order.get("discount_price", 0.0) or 0.0
        net_total = order_total - discount
        previous_refund = order.get("refund_price", 0.0) or 0.0
        max_refundable = net_total - previous_refund

        if max_refundable <= 0:
            return {"success": False, "message": "Bu sipariş için iade yapılabilecek tutar kalmadı."}

        if refund_price > max_refundable:
            return {"success": False, "message": f"İade tutarı, kalan iade edilebilir tutarı ({max_refundable:,.2f} ₺) aşamaz."}

        refund_history = json.loads(order.get("refund_history", "[]"))
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        refund_entry = {
            "date": now,
            "amount": refund_price,
            "reason": reason,
            "items": refund_items or [],
            "user": self._get_user()
        }
        refund_history.append(refund_entry)

        total_refund = order.get("refund_price", 0.0) + refund_price

        self.order_repo.update(order_id, {
            "refund_price": total_refund,
            "refund_reason": reason,
            "refund_history": json.dumps(refund_history)
        })

        if refund_items:
            order_items = self.order_item_repo.get_by_order(order_id)
            for refund_item in refund_items:
                if location_id is not None:
                    self.stock_controller.stock_in(
                        variant_id=refund_item["variant_id"],
                        location_id=location_id,
                        quantity=refund_item["quantity"],
                        reason=f"Sipariş iadesi #{order_id}",
                        reference_id=order_id
                    )
                else:
                    variant = self.variant_repo.get_by_id(refund_item["variant_id"])
                    if variant:
                        quantities = json.loads(variant.get("location_quantities", "{}"))
                        if quantities:
                            first_loc = next(iter(quantities))
                            self.stock_controller.stock_in(
                                variant_id=refund_item["variant_id"],
                                location_id=int(first_loc),
                                quantity=refund_item["quantity"],
                                reason=f"Sipariş iadesi #{order_id}",
                                reference_id=order_id
                            )

                for oi in order_items:
                    if oi["variant_ID"] == refund_item["variant_id"]:
                        new_qty = oi["quantity"] - refund_item["quantity"]
                        if new_qty <= 0:
                            self.order_item_repo.delete(oi["ID"])
                        else:
                            self.order_item_repo.update(oi["ID"], {"quantity": new_qty})
                            oi["quantity"] = new_qty
                        break

        self.logger.info(self._get_user(), "OrderController", "Sipariş iadesi yapıldı", {
            "order_id": order_id,
            "refund_price": refund_price,
            "total_refund": total_refund,
            "reason": reason
        })

        return {"success": True, "message": f"{refund_price} tutarında iade yapıldı", "total_refund": total_refund}

    def add_payment(self, order_id: int, method: str, amount: float,
                    note: str = "") -> dict:

        if not self.session.has_permission("payment_manage"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok", "payment_id": None}

        order = self.order_repo.get_by_id(order_id)
        if order is None:
            return {"success": False, "message": "Sipariş bulunamadı", "payment_id": None}

        if amount <= 0:
            return {"success": False, "message": "Ödeme tutarı 0'dan büyük olmalıdır", "payment_id": None}

        valid_methods = ["cash", "credit_card", "debit_card", "bank_transfer", "other"]
        if method not in valid_methods:
            return {"success": False, "message": f"Geçersiz ödeme yöntemi. Geçerli: {', '.join(valid_methods)}", "payment_id": None}

        order_total = self.order_item_repo.get_order_total(order_id)
        paid_total = self.payment_repo.get_order_paid_total(order_id)
        discount = order.get("discount_price", 0.0) or 0.0
        net_total = order_total - discount
        remaining = net_total - paid_total

        if remaining <= 0:
            return {"success": False, "message": "Bu sipariş için ödeme tamamlanmış, ek ödeme alınamaz.", "payment_id": None}

        if amount > remaining:
            return {"success": False, "message": f"Ödeme tutarı kalan borçtan ({remaining:,.2f} ₺) fazla olamaz.", "payment_id": None}

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        payment_id = self.payment_repo.insert({
            "order_ID": order_id,
            "method": method,
            "amount": amount,
            "status": "completed",
            "payment_date": now,
            "note": note
        })

        self.logger.info(self._get_user(), "OrderController", "Ödeme alındı", {
            "payment_id": payment_id,
            "order_id": order_id,
            "method": method,
            "amount": amount
        })

        return {"success": True, "message": "Ödeme başarıyla kaydedildi", "payment_id": payment_id}

    def get_order_payment_summary(self, order_id: int) -> dict:
        order = self.order_repo.get_by_id(order_id)
        if order is None:
            return {"success": False, "message": "Sipariş bulunamadı", "data": None}

        order_total = self.order_item_repo.get_order_total(order_id)
        paid_total = self.payment_repo.get_order_paid_total(order_id)
        discount = order.get("discount_price", 0.0) or 0.0
        refund = order.get("refund_price", 0.0) or 0.0
        net_total = order_total - discount
        remaining = net_total - paid_total
        max_refundable = net_total - refund

        payments = self.payment_repo.get_by_order(order_id)

        return {
            "success": True,
            "message": "",
            "data": {
                "order_total": order_total,
                "discount": discount,
                "net_total": net_total,
                "paid_total": paid_total,
                "refund_total": refund,
                "remaining": remaining,
                "max_refundable": max_refundable,
                "payments": payments
            }
        }

    def get_order(self, order_id: int) -> dict:
        order = self.order_repo.get_by_id(order_id)
        if order is None:
            return {"success": False, "message": "Sipariş bulunamadı", "data": None}

        order["items"] = self.order_item_repo.get_by_order(order_id)
        order["payments"] = self.payment_repo.get_by_order(order_id)
        order["refund_history"] = json.loads(order.get("refund_history", "[]"))

        return {"success": True, "message": "", "data": order}

    def get_all_orders(self) -> dict:
        orders = self.order_repo.get_all()
        return {"success": True, "message": "", "data": orders}

    def get_orders_by_status(self, status: str) -> dict:
        orders = self.order_repo.get_by_status(status)
        return {"success": True, "message": "", "data": orders}

    def get_orders_by_customer(self, customer_id: int) -> dict:
        orders = self.order_repo.get_by_customer(customer_id)
        return {"success": True, "message": "", "data": orders}

    def get_orders_by_date(self, start_date: str, end_date: str) -> dict:
        orders = self.order_repo.get_by_date_range(start_date, end_date)
        return {"success": True, "message": "", "data": orders}

    def get_pending_orders(self) -> dict:
        orders = self.order_repo.get_pending_orders()
        return {"success": True, "message": "", "data": orders}

    def add_order_item(self, order_id: int, variant_id: int, quantity: int,
                       unit_price: float, location_id: int = None) -> dict:
        if not self.session.has_permission("order_update"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        order = self.order_repo.get_by_id(order_id)
        if order is None:
            return {"success": False, "message": "Sipariş bulunamadı"}

        if order["status"] in ("cancelled", "completed", "delivered"):
            return {"success": False, "message": "Bu durumdaki siparişe kalem eklenemez"}

        variant = self.variant_repo.get_by_id(variant_id)
        if variant is None:
            return {"success": False, "message": "Varyant bulunamadı"}

        product = self.product_repo.get_by_id(variant["product_ID"])
        quantities = json.loads(variant.get("location_quantities", "{}"))

        if location_id is not None:
            available = quantities.get(str(location_id), 0)
            if available < quantity:
                return {"success": False, "message": f"Yetersiz stok — Mevcut: {available}, İstenen: {quantity}"}
            self.stock_controller.stock_out(variant_id, location_id, quantity,
                                            f"Sipariş #{order_id} kalem ekleme", order_id)
        else:
            total_available = sum(quantities.values())
            if total_available < quantity:
                return {"success": False, "message": f"Yetersiz stok — Toplam: {int(total_available)}, İstenen: {quantity}"}
            remaining = quantity
            for loc_str, loc_qty in sorted(quantities.items(), key=lambda x: -x[1]):
                if remaining <= 0:
                    break
                deduct = min(remaining, int(loc_qty))
                if deduct > 0:
                    self.stock_controller.stock_out(variant_id, int(loc_str), deduct,
                                                   f"Sipariş #{order_id} kalem ekleme", order_id)
                    remaining -= deduct

        item_id = self.order_item_repo.insert({
            "order_ID": order_id,
            "product_ID": product["ID"] if product else 0,
            "variant_ID": variant_id,
            "quantity": quantity,
            "unit_price": unit_price,
            "product_name": product["name"] if product else "?"
        })

        self.logger.info(self._get_user(), "OrderController", "Sipariş kalemi eklendi", {
            "order_id": order_id, "variant_id": variant_id, "quantity": quantity
        })

        return {"success": True, "message": "Kalem eklendi", "item_id": item_id}

    def remove_order_item(self, order_item_id: int, return_location_id: int = None,
                          quantity: int = None) -> dict:
        if not self.session.has_permission("order_update"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        item = self.order_item_repo.get_by_id(order_item_id)
        if item is None:
            return {"success": False, "message": "Sipariş kalemi bulunamadı"}

        order = self.order_repo.get_by_id(item["order_ID"])
        if order and order["status"] in ("cancelled", "completed", "delivered"):
            return {"success": False, "message": "Bu durumdaki siparişten kalem çıkarılamaz"}

        remove_qty = quantity if quantity is not None else item["quantity"]
        if remove_qty > item["quantity"]:
            remove_qty = item["quantity"]
        if remove_qty <= 0:
            return {"success": False, "message": "Geçersiz miktar"}

        if return_location_id is not None:
            self.stock_controller.stock_in(
                variant_id=item["variant_ID"],
                location_id=return_location_id,
                quantity=remove_qty,
                reason=f"Sipariş #{item['order_ID']} kalem çıkarma",
                reference_id=item["order_ID"]
            )
        else:
            variant = self.variant_repo.get_by_id(item["variant_ID"])
            if variant:
                quantities = json.loads(variant.get("location_quantities", "{}"))
                if quantities:
                    first_loc = next(iter(quantities))
                    self.stock_controller.stock_in(
                        variant_id=item["variant_ID"],
                        location_id=int(first_loc),
                        quantity=remove_qty,
                        reason=f"Sipariş #{item['order_ID']} kalem çıkarma",
                        reference_id=item["order_ID"]
                    )

        if remove_qty >= item["quantity"]:
            self.order_item_repo.delete(order_item_id)
            msg = "Kalem silindi"
        else:
            new_qty = item["quantity"] - remove_qty
            self.order_item_repo.update(order_item_id, {"quantity": new_qty})
            msg = f"{remove_qty} adet çıkarıldı, kalan: {new_qty}"

        self.logger.info(self._get_user(), "OrderController", "Sipariş kalemi güncellendi", {
            "order_item_id": order_item_id, "order_id": item["order_ID"],
            "removed_qty": remove_qty
        })

        return {"success": True, "message": msg}

    def update_order_discount(self, order_id: int, discount_price: float) -> dict:
        if not self.session.has_permission("order_update"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        order = self.order_repo.get_by_id(order_id)
        if order is None:
            return {"success": False, "message": "Sipariş bulunamadı"}

        self.order_repo.update(order_id, {"discount_price": discount_price})

        self.logger.info(self._get_user(), "OrderController", "Sipariş indirimi güncellendi", {
            "order_id": order_id, "discount": discount_price
        })

        return {"success": True, "message": f"{discount_price:,.2f} ₺ indirim uygulandı"}