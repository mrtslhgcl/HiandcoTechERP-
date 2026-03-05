from datetime import datetime

class UserModel:
    def __init__(self):
        self.ID : int
        self.username : str
        self.password_hash : str
        self.employee_ID : int
        self.role_ID : int
        self.is_active : bool = None
        self.created_at : datetime