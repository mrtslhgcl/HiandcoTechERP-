from datetime import datetime

class PermissionModel:
    def __init__(self):
        self.ID : int
        self.key : str
        self.description : str = ""
        self.created_at : datetime