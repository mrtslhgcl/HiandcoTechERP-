from models.variant_value_model import VariantValueModel
from datetime import datetime

class VariantModel:
    def __init__(self):
        self.ID : int
        self.product_ID : int
        self.sku : str
        self.barcode : str
        self.buy_price : float
        self.sell_price : float
        self.vat_included : bool
        self.vat_rate : float
        self.attributes : list[VariantValueModel] = []
        self.created_at : datetime
        self.location_quantities : dict[int, int] = {}
        
    @property
    def total_quantity(self):
        return sum(self.location_quantities.values())