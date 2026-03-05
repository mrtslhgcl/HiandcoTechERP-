from datetime import datetime

class RoleModel:
    def __init__(self):
        self.ID : int
        self.name : str
        self.description : str = ""
        self.created_at : datetime
        self.role_permissions : dict[int, int] = {}