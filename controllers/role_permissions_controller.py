import json
from datetime import datetime
from database.roles_repository import RoleRepository
from database.permissions_repository import PermissionRepository
from database.employee_role_repository import EmployeeRoleRepository
from utils.logger import Logger
from utils.session import Session

class RolePermissionController:
    def __init__(self):
        self.role_repo = RoleRepository()
        self.permission_repo = PermissionRepository()
        self.employee_role_repo = EmployeeRoleRepository()
        self.logger = Logger()
        self.session = Session()

    def _get_user(self) -> str:
        return self.session.get_log_user()

    def add_permission(self, key: str, description: str = "") -> dict:
        if not self.session.has_permission("permission_manage"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        existing = self.permission_repo.get_by_key(key)
        if existing:
            return {"success": False, "message": "Bu yetki anahtarı zaten mevcut", "permission_id": None}

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        permission_id = self.permission_repo.insert({
            "key": key,
            "description": description,
            "created_at": now
        })

        self.logger.info(self._get_user(), "RolePermissionController", "Yetki eklendi", {
            "permission_id": permission_id,
            "key": key
        })

        return {"success": True, "message": "Yetki başarıyla eklendi", "permission_id": permission_id}

    def update_permission(self, permission_id: int, data: dict) -> dict:
        if not self.session.has_permission("permission_manage"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        permission = self.permission_repo.get_by_id(permission_id)
        if permission is None:
            return {"success": False, "message": "Yetki bulunamadı"}

        if "key" in data and data["key"] != permission["key"]:
            existing = self.permission_repo.get_by_key(data["key"])
            if existing:
                return {"success": False, "message": "Bu yetki anahtarı zaten mevcut"}

        self.permission_repo.update(permission_id, data)

        self.logger.info(self._get_user(), "RolePermissionController", "Yetki güncellendi", {
            "permission_id": permission_id,
            "updated_fields": list(data.keys())
        })

        return {"success": True, "message": "Yetki başarıyla güncellendi"}

    def delete_permission(self, permission_id: int) -> dict:
        if not self.session.has_permission("permission_manage"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        permission = self.permission_repo.get_by_id(permission_id)
        if permission is None:
            return {"success": False, "message": "Yetki bulunamadı"}

        all_roles = self.role_repo.get_all()
        for role in all_roles:
            perm_ids = json.loads(role.get("permission_IDs", "[]"))
            if permission_id in perm_ids:
                return {"success": False, "message": f"Bu yetki '{role['name']}' rolünde kullanılıyor. Önce rolden kaldırın."}

        self.permission_repo.delete(permission_id)

        self.logger.info(self._get_user(), "RolePermissionController", "Yetki silindi", {
            "permission_id": permission_id,
            "key": permission["key"]
        })

        return {"success": True, "message": "Yetki başarıyla silindi"}

    def get_permission(self, permission_id: int) -> dict:
        permission = self.permission_repo.get_by_id(permission_id)
        if permission is None:
            return {"success": False, "message": "Yetki bulunamadı", "data": None}

        return {"success": True, "message": "", "data": permission}

    def get_all_permissions(self) -> dict:
        permissions = self.permission_repo.get_all()
        return {"success": True, "message": "", "data": permissions}

    def add_role(self, name: str, description: str = "", permission_ids: list[int] = None) -> dict:
        if not self.session.has_permission("role_manage"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        existing = self.role_repo.get_by_name(name)
        if existing:
            return {"success": False, "message": "Bu rol adı zaten mevcut", "role_id": None}

        if permission_ids is None:
            permission_ids = []

        for pid in permission_ids:
            perm = self.permission_repo.get_by_id(pid)
            if perm is None:
                return {"success": False, "message": f"Yetki bulunamadı: ID {pid}", "role_id": None}

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        role_id = self.role_repo.insert({
            "name": name,
            "description": description,
            "permission_IDs": json.dumps(permission_ids),
            "created_at": now
        })

        self.logger.info(self._get_user(), "RolePermissionController", "Rol eklendi", {
            "role_id": role_id,
            "name": name,
            "permission_count": len(permission_ids)
        })

        return {"success": True, "message": "Rol başarıyla eklendi", "role_id": role_id}

    def update_role(self, role_id: int, data: dict) -> dict:
        if not self.session.has_permission("role_manage"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        role = self.role_repo.get_by_id(role_id)
        if role is None:
            return {"success": False, "message": "Rol bulunamadı"}

        if "name" in data and data["name"] != role["name"]:
            existing = self.role_repo.get_by_name(data["name"])
            if existing:
                return {"success": False, "message": "Bu rol adı zaten mevcut"}

        if "permission_IDs" in data:
            perm_ids = data["permission_IDs"]
            if isinstance(perm_ids, list):
                for pid in perm_ids:
                    perm = self.permission_repo.get_by_id(pid)
                    if perm is None:
                        return {"success": False, "message": f"Yetki bulunamadı: ID {pid}"}
                data["permission_IDs"] = json.dumps(perm_ids)

        self.role_repo.update(role_id, data)

        self.logger.info(self._get_user(), "RolePermissionController", "Rol güncellendi", {
            "role_id": role_id,
            "updated_fields": list(data.keys())
        })

        return {"success": True, "message": "Rol başarıyla güncellendi"}

    def delete_role(self, role_id: int) -> dict:
        if not self.session.has_permission("role_manage"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        role = self.role_repo.get_by_id(role_id)
        if role is None:
            return {"success": False, "message": "Rol bulunamadı"}

        assigned = self.employee_role_repo.get_employees_by_role(role_id)
        if assigned:
            return {"success": False, "message": f"Bu rol {len(assigned)} çalışana atanmış. Önce atamalarını kaldırın."}

        self.role_repo.delete(role_id)

        self.logger.info(self._get_user(), "RolePermissionController", "Rol silindi", {
            "role_id": role_id,
            "name": role["name"]
        })

        return {"success": True, "message": "Rol başarıyla silindi"}

    def get_role(self, role_id: int) -> dict:
        role = self.role_repo.get_by_id(role_id)
        if role is None:
            return {"success": False, "message": "Rol bulunamadı", "data": None}

        perm_ids = json.loads(role.get("permission_IDs", "[]"))
        permissions = []
        for pid in perm_ids:
            perm = self.permission_repo.get_by_id(pid)
            if perm:
                permissions.append(perm)
        role["permissions_detail"] = permissions

        return {"success": True, "message": "", "data": role}

    def get_all_roles(self) -> dict:
        roles = self.role_repo.get_all()
        return {"success": True, "message": "", "data": roles}
    
    def assign_role_to_employee(self, employee_id: int, role_id: int) -> dict:

        if not self.session.has_permission("role_assign"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        role = self.role_repo.get_by_id(role_id)
        if role is None:
            return {"success": False, "message": "Rol bulunamadı"}

        existing = self.employee_role_repo.get_roles_by_employee(employee_id)
        for er in existing:
            if er["role_ID"] == role_id:
                return {"success": False, "message": "Bu rol zaten bu çalışana atanmış"}

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.employee_role_repo.assign_role(employee_id, role_id, now)

        self.logger.info(self._get_user(), "RolePermissionController", "Rol atandı", {
            "employee_id": employee_id,
            "role_id": role_id,
            "role_name": role["name"]
        })

        return {"success": True, "message": "Rol başarıyla atandı"}

    def remove_role_from_employee(self, employee_id: int, role_id: int) -> dict:
        if not self.session.has_permission("role_assign"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        role = self.role_repo.get_by_id(role_id)
        if role is None:
            return {"success": False, "message": "Rol bulunamadı"}

        removed = self.employee_role_repo.remove_role(employee_id, role_id)
        if not removed:
            return {"success": False, "message": "Bu çalışanda bu rol atanmamış"}

        self.logger.info(self._get_user(), "RolePermissionController", "Rol kaldırıldı", {
            "employee_id": employee_id,
            "role_id": role_id,
            "role_name": role["name"]
        })

        return {"success": True, "message": "Rol başarıyla kaldırıldı"}

    def get_employee_roles(self, employee_id: int) -> dict:
        employee_roles = self.employee_role_repo.get_roles_by_employee(employee_id)
        roles = []
        for er in employee_roles:
            role = self.role_repo.get_by_id(er["role_ID"])
            if role:
                roles.append(role)

        return {"success": True, "message": "", "data": roles}

    def get_employee_permissions(self, employee_id: int) -> dict:
        result = self.get_employee_roles(employee_id)
        roles = result["data"]
        permissions = set()

        for role in roles:
            perm_ids = json.loads(role.get("permission_IDs", "[]"))
            for pid in perm_ids:
                perm = self.permission_repo.get_by_id(pid)
                if perm:
                    permissions.add(perm["key"])

        return {"success": True, "message": "", "data": list(permissions)}

    def add_permission_to_role(self, role_id: int, permission_id: int) -> dict:
        if not self.session.has_permission("role_manage"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        role = self.role_repo.get_by_id(role_id)
        if role is None:
            return {"success": False, "message": "Rol bulunamadı"}

        permission = self.permission_repo.get_by_id(permission_id)
        if permission is None:
            return {"success": False, "message": "Yetki bulunamadı"}

        perm_ids = json.loads(role.get("permission_IDs", "[]"))
        if permission_id in perm_ids:
            return {"success": False, "message": "Bu yetki zaten bu rolde mevcut"}

        perm_ids.append(permission_id)
        self.role_repo.update(role_id, {"permission_IDs": json.dumps(perm_ids)})

        self.logger.info(self._get_user(), "RolePermissionController", "Role yetki eklendi", {
            "role_id": role_id,
            "role_name": role["name"],
            "permission_id": permission_id,
            "permission_key": permission["key"]
        })

        return {"success": True, "message": "Yetki role başarıyla eklendi"}

    def remove_permission_from_role(self, role_id: int, permission_id: int) -> dict:
        if not self.session.has_permission("role_manage"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        role = self.role_repo.get_by_id(role_id)
        if role is None:
            return {"success": False, "message": "Rol bulunamadı"}

        perm_ids = json.loads(role.get("permission_IDs", "[]"))
        if permission_id not in perm_ids:
            return {"success": False, "message": "Bu yetki bu rolde mevcut değil"}

        perm_ids.remove(permission_id)
        self.role_repo.update(role_id, {"permission_IDs": json.dumps(perm_ids)})

        self.logger.info(self._get_user(), "RolePermissionController", "Rolden yetki kaldırıldı", {
            "role_id": role_id,
            "role_name": role["name"],
            "permission_id": permission_id
        })

        return {"success": True, "message": "Yetki rolden başarıyla kaldırıldı"}