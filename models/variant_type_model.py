from datetime import datetime
from models.variant_value_model import VariantValueModel
class VariantTypeModel:
    def __init__(self):
        self.ID : int
        self.name : str
        self.values : list[VariantValueModel] = []
        self.created_at : datetime