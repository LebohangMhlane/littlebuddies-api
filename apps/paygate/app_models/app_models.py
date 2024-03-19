
from apps.merchants.models import Merchant

# what the app sends to the server to initiate payment after checkout:

class CheckoutFormData():
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

    def getMerchant(self) -> Merchant:
        if self.merchantId is not None:
            merchant = Merchant.objects.get(id=self.merchantId)
            return merchant
        
    def convertAmountToDecimal(self):
        return float(self.amount)