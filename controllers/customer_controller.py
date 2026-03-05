from datetime import datetime
from database.customer_repository import CustomerRepository
from database.order_repository import OrderRepository
from utils.logger import Logger
from utils.session import Session


class CustomerController:
    def __init__(self):
        self.customer_repo = CustomerRepository()
        self.order_repo = OrderRepository()
        self.logger = Logger()
        self.session = Session()

    def _get_user(self) -> str:
        return self.session.get_log_user()

    def add_customer(self, first_name: str, last_name: str, email: str = "",
                     phone_number: str = "", address: str = "",
                     notes: str = "") -> dict:

        if not self.session.has_permission("customer_create"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok", "customer_id": None}

        if email:
            existing = self.customer_repo.get_by_email(email)
            if existing:
                return {"success": False, "message": "Bu e-posta adresi zaten kayıtlı", "customer_id": None}

        if phone_number:
            existing = self.customer_repo.get_by_phone(phone_number)
            if existing:
                return {"success": False, "message": "Bu telefon numarası zaten kayıtlı", "customer_id": None}

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        customer_id = self.customer_repo.insert({
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone_number": phone_number,
            "address": address,
            "notes": notes,
            "is_active": 1,
            "created_at": now
        })

        self.logger.info(self._get_user(), "CustomerController", "Müşteri eklendi", {
            "customer_id": customer_id,
            "name": f"{first_name} {last_name}"
        })

        return {"success": True, "message": "Müşteri başarıyla eklendi", "customer_id": customer_id}

    def update_customer(self, customer_id: int, data: dict) -> dict:
        if not self.session.has_permission("customer_update"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        customer = self.customer_repo.get_by_id(customer_id)
        if customer is None:
            return {"success": False, "message": "Müşteri bulunamadı"}

        if "email" in data and data["email"] and data["email"] != customer.get("email", ""):
            existing = self.customer_repo.get_by_email(data["email"])
            if existing:
                return {"success": False, "message": "Bu e-posta adresi zaten kayıtlı"}

        if "phone_number" in data and data["phone_number"] and data["phone_number"] != customer.get("phone_number", ""):
            existing = self.customer_repo.get_by_phone(data["phone_number"])
            if existing:
                return {"success": False, "message": "Bu telefon numarası zaten kayıtlı"}

        self.customer_repo.update(customer_id, data)

        self.logger.info(self._get_user(), "CustomerController", "Müşteri güncellendi", {
            "customer_id": customer_id,
            "updated_fields": list(data.keys())
        })

        return {"success": True, "message": "Müşteri başarıyla güncellendi"}

    def delete_customer(self, customer_id: int) -> dict:
        if not self.session.has_permission("customer_delete"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        customer = self.customer_repo.get_by_id(customer_id)
        if customer is None:
            return {"success": False, "message": "Müşteri bulunamadı"}

        orders = self.order_repo.get_by_customer(customer_id)
        if orders:
            return {"success": False, "message": f"Bu müşterinin {len(orders)} siparişi var. Silme yerine pasife alın."}

        self.customer_repo.delete(customer_id)

        self.logger.info(self._get_user(), "CustomerController", "Müşteri silindi", {
            "customer_id": customer_id,
            "name": f"{customer['first_name']} {customer['last_name']}"
        })

        return {"success": True, "message": "Müşteri başarıyla silindi"}

    def deactivate_customer(self, customer_id: int) -> dict:
        if not self.session.has_permission("customer_update"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        customer = self.customer_repo.get_by_id(customer_id)
        if customer is None:
            return {"success": False, "message": "Müşteri bulunamadı"}

        self.customer_repo.update(customer_id, {"is_active": 0})

        self.logger.info(self._get_user(), "CustomerController", "Müşteri pasife alındı", {
            "customer_id": customer_id,
            "name": f"{customer['first_name']} {customer['last_name']}"
        })

        return {"success": True, "message": "Müşteri pasife alındı"}

    def activate_customer(self, customer_id: int) -> dict:
        if not self.session.has_permission("customer_update"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        customer = self.customer_repo.get_by_id(customer_id)
        if customer is None:
            return {"success": False, "message": "Müşteri bulunamadı"}

        self.customer_repo.update(customer_id, {"is_active": 1})

        self.logger.info(self._get_user(), "CustomerController", "Müşteri aktife alındı", {
            "customer_id": customer_id,
            "name": f"{customer['first_name']} {customer['last_name']}"
        })

        return {"success": True, "message": "Müşteri aktife alındı"}

    def get_customer(self, customer_id: int) -> dict:
        customer = self.customer_repo.get_by_id(customer_id)
        if customer is None:
            return {"success": False, "message": "Müşteri bulunamadı", "data": None}

        return {"success": True, "message": "", "data": customer}

    def get_all_customers(self) -> dict:
        customers = self.customer_repo.get_all()
        return {"success": True, "message": "", "data": customers}

    def get_active_customers(self) -> dict:
        customers = self.customer_repo.get_active_customers()
        return {"success": True, "message": "", "data": customers}

    def search_customers(self, keyword: str) -> dict:
        customers = self.customer_repo.search_by_name(keyword)
        return {"success": True, "message": "", "data": customers}

    def get_customer_by_email(self, email: str) -> dict:
        customer = self.customer_repo.get_by_email(email)
        if customer is None:
            return {"success": False, "message": "Müşteri bulunamadı", "data": None}

        return {"success": True, "message": "", "data": customer}

    def get_customer_by_phone(self, phone_number: str) -> dict:
        customer = self.customer_repo.get_by_phone(phone_number)
        if customer is None:
            return {"success": False, "message": "Müşteri bulunamadı", "data": None}

        return {"success": True, "message": "", "data": customer}

    def get_customer_orders(self, customer_id: int) -> dict:
        customer = self.customer_repo.get_by_id(customer_id)
        if customer is None:
            return {"success": False, "message": "Müşteri bulunamadı", "data": None}

        orders = self.order_repo.get_by_customer(customer_id)
        return {"success": True, "message": "", "data": orders}