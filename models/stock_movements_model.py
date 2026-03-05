from datetime import datetime

MOVEMENT_TYPES = ["IN", "OUT", "ADJUSTMENT", "TRANSFER", "RETURN","OTHER"]

class StockMovementModel:
    def __init__(self):
        self.ID : int
        self.variant_ID : int
        self.qty_delta : int
        self.movement_type : str = MOVEMENT_TYPES[0]
        self.description : str = ""
        self.reference_type : str = ""
        self.before_qty : int
        self.after_qty : int
        self.created_by_user_ID : int = None
        self.created_at : datetime