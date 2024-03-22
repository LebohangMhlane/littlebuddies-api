
from apps.merchants.models import Merchant

# what the mobile app sends to the server to initiate payment after checkout:

class CheckoutFormPayload():
    merchantId = None
    totalCheckoutAmount = 0
    products = []
    discountTotal = 0
    
    def __init__(self, payload):
        payload = payload.copy()
        self.merchantId = int(payload.get("merchantId"))
        self.totalCheckoutAmount = int(payload.get("totalCheckoutAmount"))
        self.products = payload.get("items")
        self.discountTotal = int(payload.get("discountTotal"))
        
    def convertAmountToDecimal(self):
        return float(self.amount)
    
    def verifyPurchase(self, checkoutFormData):
        # TODO: verify the purchase:
        return True
    