
from apps.merchants.models import Merchant

# what the app sends to the server to initiate payment after checkout:
class CheckoutFormPayload():
    merchantId = None
    totalCheckoutAmount = 0
    items = []
    
    def __init__(self, payload:dict):
        self.merchantId = int(payload.get("merchantId"))
        self.totalCheckoutAmount = int(payload.get("totalCheckoutAmount"))
        self.items = payload.get("items")

    def getMerchant(self) -> Merchant:
        if self.merchantId is not None:
            merchant = Merchant.objects.get(id=self.merchantId)
            return merchant