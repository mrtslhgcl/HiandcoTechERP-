from datetime import datetime

class VariantValueModel:
    def __init__(self):
        self.ID : int
        self.variant_type_ID : int
        self.value : str
        self.created_at : datetime