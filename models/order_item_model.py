class OrderItemModel:
    def __init__(self):
        self.ID : int
        self.order_ID : int
        self.product_ID : int
        self.variant_ID : int
        self.quantity : int = 1
        self.unit_price : float = 0.0
        self.product_name : str = ""
    
    @property
    def total_price(self):
        return self.quantity * self.unit_price