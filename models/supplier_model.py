from datetime import datetime

class SupplierModel:
    def __init__(self):
        self.ID : int
        self.name : str
        self.description : str = ""
        self.email : str = ""
        self.phone : str = ""
        self.address : str = ""
        self.authorized_person : str = ""
        self.IBAN : str = ""
        self.logo : str = ""
        self.created_at : datetime
        
