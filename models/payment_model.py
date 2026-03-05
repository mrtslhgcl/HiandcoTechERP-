from datetime import datetime

class PaymentModel:
    def __init__(self):
        self.ID : int
        self.order_ID : int
        self.method : str
        self.amount : float
        self.status : str = ""
        self.payment_date : datetime = None
        self.note : str = ""