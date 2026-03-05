from datetime import datetime
from models.order_item_model import OrderItemModel
from models.customer_model import CustomerModel
from models.payment_model import PaymentModel

ORDER_STATUS = ["pending", "processing", "shipped", "delivered", "cancelled"]
PAYMENT_METHODS = ["credit_card", "debit_card", "paypal", "bank_transfer", "cash_on_delivery"]
PAYMENT_STATUS = ["unpaid", "paid", "refunded", "partially_refunded", "failed"]
SHIPPING_METHODS = ["standard_shipping", "express_shipping", "pickup", "drone_delivery"]
CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CNY", "TRY", "AUD", "CAD", "CHF", "SEK"]

class OrderModel:
    def __init__(self):
        self.ID : int
        self.items : list[OrderItemModel] = []
        self.number_of_installments : int = 1
        self.paid_price : float = 0.0
        self.currency : str = CURRENCIES[5] 
        self.created_at : datetime
        self.customer_ID : int = 0
        self.shipping_address : str = "In-store Pickup"
        self.billing_address : str = "In-store Pickup"
        self.status : str = ORDER_STATUS[0]
        self.tracking_number : str = ""
        self.delivery_date : datetime = None
        self.payments : list[PaymentModel] = []
        self.refund_price : float = 0.0
        self.refund_reason : str = ""
        self.refund_history : list[dict] = []
        self.cancellation_reason : str = ""
        self.cancellation_date : datetime = None
        self.notes : str = ""
        self.is_gift : bool = False
        self.gift_message : str = ""
        self.discount_code : str = ""
        self.discount_price : float = 0.0
        self.total_weight : float = 0.0
        self.total_volume : float = 0.0
        self.shipping_method : str = SHIPPING_METHODS[0]
        self.shipping_cost : float = 0.0
    
    @property
    def total_price(self):
        return sum(item.total_price for item in self.items)