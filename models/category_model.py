from datetime import datetime

class CategoryModel:
    def __init__(self):
        self.ID : int
        self.name : str
        self.description : str = ""
        self.parent_category_ID : int = None
        self.created_at : datetime