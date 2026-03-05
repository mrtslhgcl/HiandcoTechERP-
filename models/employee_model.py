from datetime import datetime


class EmployeeModel:
    def __init__(self):
        self.ID : int
        self.employee_code : str
        self.first_name : str
        self.last_name : str
        self.photo_path : str = ""
        self.status : bool = True
        self.created_at : datetime
        self.email : str = ""
        self.phone_number : str = ""
        self.address : str = ""
        self.notes : str = ""