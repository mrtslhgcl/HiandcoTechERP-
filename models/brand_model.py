from datetime import datetime

class BrandModel:
    def __init__(self):
        self.ID : int
        self.name : str
        self.description : str = ""
        self.logo : str = ""
        self.created_at : datetime