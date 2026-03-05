class Session:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.user_id: int = None
        self.username: str = None
        self.employee_id: int = None
        self.employee_name: str = None
        self.roles: list[dict] = []
        self.permissions: list[str] = []
        self.is_logged_in: bool = False

    def set_session(self, user: dict, employee: dict, roles: list[dict], permissions: list[str]):
        self.user_id = user["ID"]
        self.username = user["username"]
        self.employee_id = employee["ID"]
        self.employee_name = f"{employee['first_name']} {employee['last_name']}"
        self.roles = roles
        self.permissions = permissions
        self.is_logged_in = True

    def clear(self):
        self.user_id = None
        self.username = None
        self.employee_id = None
        self.employee_name = None
        self.roles = []
        self.permissions = []
        self.is_logged_in = False

    def has_permission(self, permission_key: str) -> bool:
        if not self.is_logged_in:
            return False
        if self.is_admin():
            return True
        return permission_key in self.permissions

    def is_admin(self) -> bool:
        return any(r.get("name", "").lower() == "admin" for r in self.roles)

    def get_display_name(self) -> str:
        return self.employee_name if self.employee_name else "Bilinmeyen"

    def get_log_user(self) -> str:
        return self.username if self.username else "system"