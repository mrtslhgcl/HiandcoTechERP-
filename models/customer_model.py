from datetime import datetime

class CustomerModel:
    def __init__(self):
        self.ID : int
        self.name : str
        self.email : str = ""
        self.phone : str = ""
        self.address : str = ""
        self.created_at : datetime
        self.orders : list[int] = []
        self.is_company : bool = False
        self.company_name : str = ""
        self.tax_number : str = ""
        self.notes : str = ""
        