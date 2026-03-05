import hashlib
from datetime import datetime
from database.user_repository import UserRepository
from database.employee_repository import EmployeeRepository
from database.employee_role_repository import EmployeeRoleRepository
from database.roles_repository import RoleRepository
from database.permissions_repository import PermissionRepository
from utils.logger import Logger
from utils.session import Session
import json

class AuthController:
    def __init__(self):
        self.user_repo = UserRepository()
        self.employee_repo = EmployeeRepository()
        self.employee_role_repo = EmployeeRoleRepository()
        self.role_repo = RoleRepository()
        self.permission_repo = PermissionRepository()
        self.logger = Logger()
        self.session = Session()

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def login(self, username: str, password: str) -> dict:
        user = self.user_repo.get_by_username(username)
        if user is None:
            self.logger.warning("system", "AuthController", "Başarısız giriş - kullanıcı bulunamadı", {"username": username})
            return {"success": False, "message": "Kullanıcı adı veya şifre hatalı"}

        if not user["is_active"]:
            self.logger.warning("system", "AuthController", "Başarısız giriş - kullanıcı pasif", {"username": username})
            return {"success": False, "message": "Bu hesap devre dışı bırakılmış"}

        password_hash = self._hash_password(password)
        if user["password_hash"] != password_hash:
            self.logger.warning("system", "AuthController", "Başarısız giriş - şifre hatalı", {"username": username})
            return {"success": False, "message": "Kullanıcı adı veya şifre hatalı"}

        employee = self.employee_repo.get_by_id(user["employee_ID"])
        if employee is None:
            self.logger.error("system", "AuthController", "Çalışan bulunamadı", {"employee_ID": user["employee_ID"]})
            return {"success": False, "message": "Çalışan kaydı bulunamadı"}

        if not employee["status"]:
            self.logger.warning("system", "AuthController", "Başarısız giriş - çalışan pasif", {"username": username})
            return {"success": False, "message": "Bu çalışan hesabı devre dışı"}

        roles, permissions = self._load_roles_and_permissions(employee["ID"])

        self.session.set_session(user, employee, roles, permissions)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.user_repo.update_last_login(user["ID"], now)

        self.logger.info(self.session.get_log_user(), "AuthController", "Giriş başarılı", {
            "user_id": user["ID"],
            "employee": self.session.get_display_name()
        })

        return {"success": True, "message": "Giriş başarılı"}

    def logout(self):
        username = self.session.get_log_user()
        self.logger.info(username, "AuthController", "Çıkış yapıldı")
        self.session.clear()

    def _load_roles_and_permissions(self, employee_id: int) -> tuple[list[dict], list[str]]:
        roles = []
        permissions = set()

        employee_roles = self.employee_role_repo.get_roles_by_employee(employee_id)

        for er in employee_roles:
            role = self.role_repo.get_by_id(er["role_ID"])
            if role is None:
                continue
            roles.append(role)

            permission_ids = json.loads(role.get("permission_IDs", "[]"))
            for pid in permission_ids:
                perm = self.permission_repo.get_by_id(pid)
                if perm:
                    permissions.add(perm["key"])

        return roles, list(permissions)

    def register_user(self, employee_id: int, username: str, password: str) -> dict:
        existing = self.user_repo.get_by_username(username)
        if existing:
            return {"success": False, "message": "Bu kullanıcı adı zaten kullanılıyor", "user_id": None}

        employee = self.employee_repo.get_by_id(employee_id)
        if employee is None:
            return {"success": False, "message": "Çalışan bulunamadı", "user_id": None}

        existing_user = self.user_repo.get_by_employee_id(employee_id)
        if existing_user:
            return {"success": False, "message": "Bu çalışanın zaten bir kullanıcı hesabı var", "user_id": None}

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        password_hash = self._hash_password(password)

        user_id = self.user_repo.insert({
            "employee_ID": employee_id,
            "username": username,
            "password_hash": password_hash,
            "is_active": 1,
            "created_at": now
        })

        log_user = self.session.get_log_user() if self.session.is_logged_in else "system"
        self.logger.info(log_user, "AuthController", "Yeni kullanıcı oluşturuldu", {
            "user_id": user_id,
            "username": username,
            "employee_id": employee_id
        })

        return {"success": True, "message": "Kullanıcı başarıyla oluşturuldu", "user_id": user_id}

    def change_password(self, user_id: int, old_password: str, new_password: str) -> dict:
        user = self.user_repo.get_by_id(user_id)
        if user is None:
            return {"success": False, "message": "Kullanıcı bulunamadı"}

        old_hash = self._hash_password(old_password)
        if user["password_hash"] != old_hash:
            self.logger.warning(self.session.get_log_user(), "AuthController", "Şifre değiştirme başarısız - eski şifre hatalı", {
                "user_id": user_id
            })
            return {"success": False, "message": "Mevcut şifre hatalı"}

        new_hash = self._hash_password(new_password)
        self.user_repo.update(user_id, {"password_hash": new_hash})

        self.logger.info(self.session.get_log_user(), "AuthController", "Şifre değiştirildi", {
            "user_id": user_id
        })

        return {"success": True, "message": "Şifre başarıyla değiştirildi"}

    def reset_password(self, user_id: int, new_password: str) -> dict:
        if not self.session.has_permission("user_reset_password"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        user = self.user_repo.get_by_id(user_id)
        if user is None:
            return {"success": False, "message": "Kullanıcı bulunamadı"}

        new_hash = self._hash_password(new_password)
        self.user_repo.update(user_id, {"password_hash": new_hash})

        self.logger.info(self.session.get_log_user(), "AuthController", "Şifre sıfırlandı (admin)", {
            "target_user_id": user_id,
            "target_username": user["username"]
        })

        return {"success": True, "message": "Şifre başarıyla sıfırlandı"}

    def deactivate_user(self, user_id: int) -> dict:
        if not self.session.has_permission("user_manage"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        user = self.user_repo.get_by_id(user_id)
        if user is None:
            return {"success": False, "message": "Kullanıcı bulunamadı"}

        self.user_repo.update(user_id, {"is_active": 0})

        self.logger.info(self.session.get_log_user(), "AuthController", "Kullanıcı devre dışı bırakıldı", {
            "target_user_id": user_id,
            "target_username": user["username"]
        })

        return {"success": True, "message": "Kullanıcı devre dışı bırakıldı"}

    def activate_user(self, user_id: int) -> dict:
        if not self.session.has_permission("user_manage"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        user = self.user_repo.get_by_id(user_id)
        if user is None:
            return {"success": False, "message": "Kullanıcı bulunamadı"}

        self.user_repo.update(user_id, {"is_active": 1})

        self.logger.info(self.session.get_log_user(), "AuthController", "Kullanıcı aktif edildi", {
            "target_user_id": user_id,
            "target_username": user["username"]
        })

        return {"success": True, "message": "Kullanıcı aktif edildi"}