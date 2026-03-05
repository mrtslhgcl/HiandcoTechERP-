from datetime import datetime

class EmployeeRoleModel:
    def __init__(self):
        self.ID : int
        self.name : str
        self.description : str = ""
        self.created_at : datetime
        self.authorities : list[str] = []
        