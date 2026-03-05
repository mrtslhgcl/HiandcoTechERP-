from datetime import datetime
from database.employee_repository import EmployeeRepository
from utils.logger import Logger
from utils.session import Session

class EmployeeController:
    def __init__(self):
        self.employee_repo = EmployeeRepository()
        self.logger = Logger()
        self.session = Session()

    def _get_user(self) -> str:
        return self.session.get_log_user()

    def add_employee(self, employee_code: str, first_name: str, last_name: str,
                     email: str = "", phone_number: str = "", address: str = "",
                     photo_path: str = "", notes: str = "") -> dict:

        if not self.session.has_permission("employee_create"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        existing = self.employee_repo.get_by_code(employee_code)
        if existing:
            return {"success": False, "message": "Bu çalışan kodu zaten kullanılıyor", "employee_id": None}

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        employee_id = self.employee_repo.insert({
            "employee_code": employee_code,
            "first_name": first_name,
            "last_name": last_name,
            "photo_path": photo_path,
            "status": 1,
            "created_at": now,
            "email": email,
            "phone_number": phone_number,
            "address": address,
            "notes": notes
        })

        self.logger.info(self._get_user(), "EmployeeController", "Çalışan eklendi", {
            "employee_id": employee_id,
            "employee_code": employee_code,
            "name": f"{first_name} {last_name}"
        })

        return {"success": True, "message": "Çalışan başarıyla eklendi", "employee_id": employee_id}

    def update_employee(self, employee_id: int, data: dict) -> dict:

        if not self.session.has_permission("employee_update"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        employee = self.employee_repo.get_by_id(employee_id)
        if employee is None:
            return {"success": False, "message": "Çalışan bulunamadı"}

        if "employee_code" in data and data["employee_code"] != employee["employee_code"]:
            existing = self.employee_repo.get_by_code(data["employee_code"])
            if existing:
                return {"success": False, "message": "Bu çalışan kodu zaten kullanılıyor"}

        self.employee_repo.update(employee_id, data)

        self.logger.info(self._get_user(), "EmployeeController", "Çalışan güncellendi", {
            "employee_id": employee_id,
            "updated_fields": list(data.keys())
        })

        return {"success": True, "message": "Çalışan başarıyla güncellendi"}

    def delete_employee(self, employee_id: int) -> dict:

        if not self.session.has_permission("employee_delete"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        employee = self.employee_repo.get_by_id(employee_id)
        if employee is None:
            return {"success": False, "message": "Çalışan bulunamadı"}

        self.employee_repo.delete(employee_id)

        self.logger.info(self._get_user(), "EmployeeController", "Çalışan silindi", {
            "employee_id": employee_id,
            "name": f"{employee['first_name']} {employee['last_name']}"
        })

        return {"success": True, "message": "Çalışan başarıyla silindi"}

    def get_employee(self, employee_id: int) -> dict:

        employee = self.employee_repo.get_by_id(employee_id)
        if employee is None:
            return {"success": False, "message": "Çalışan bulunamadı", "data": None}

        return {"success": True, "message": "", "data": employee}

    def get_all_employees(self) -> dict:

        employees = self.employee_repo.get_all()
        return {"success": True, "message": "", "data": employees}

    def get_active_employees(self) -> dict:

        employees = self.employee_repo.get_active_employees()
        return {"success": True, "message": "", "data": employees}

    def get_inactive_employees(self) -> dict:

        employees = self.employee_repo.get_inactive_employees()
        return {"success": True, "message": "", "data": employees}

    def search_employees(self, keyword: str) -> dict:

        employees = self.employee_repo.search_by_name(keyword)
        return {"success": True, "message": "", "data": employees}

    def deactivate_employee(self, employee_id: int) -> dict:

        if not self.session.has_permission("employee_update"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        employee = self.employee_repo.get_by_id(employee_id)
        if employee is None:
            return {"success": False, "message": "Çalışan bulunamadı"}

        self.employee_repo.update(employee_id, {"status": 0})

        self.logger.info(self._get_user(), "EmployeeController", "Çalışan pasife alındı", {
            "employee_id": employee_id,
            "name": f"{employee['first_name']} {employee['last_name']}"
        })

        return {"success": True, "message": "Çalışan pasife alındı"}

    def activate_employee(self, employee_id: int) -> dict:

        if not self.session.has_permission("employee_update"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        employee = self.employee_repo.get_by_id(employee_id)
        if employee is None:
            return {"success": False, "message": "Çalışan bulunamadı"}

        self.employee_repo.update(employee_id, {"status": 1})

        self.logger.info(self._get_user(), "EmployeeController", "Çalışan aktife alındı", {
            "employee_id": employee_id,
            "name": f"{employee['first_name']} {employee['last_name']}"
        })

        return {"success": True, "message": "Çalışan aktife alındı"}

    def get_employee_by_code(self, employee_code: str) -> dict:

        employee = self.employee_repo.get_by_code(employee_code)
        if employee is None:
            return {"success": False, "message": "Çalışan bulunamadı", "data": None}

        return {"success": True, "message": "", "data": employee}