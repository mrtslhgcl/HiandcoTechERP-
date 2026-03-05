from models.variant_model import VariantModel
from models.product_image_model import ProductImageModel
from datetime import datetime,timezone


class ProductModel:
    def __init__(self):
        self.ID : int
        self.is_active : bool = None
        self.name  : str
        self.description  : str = ""
        self.main_category_ID : int
        self.extra_category_IDs : list[int] = []
        self.brand_ID : int
        self.supplier_ID : int
        self.sale_unit : str
        self.variants : list[VariantModel] = []
        self.images : list[ProductImageModel] = []
        self.created_at : datetime