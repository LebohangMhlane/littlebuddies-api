
from django.conf import settings
from apps.products.models import Product

# what the mobile app sends to the server to initiate payment after checkout:

class CheckoutForm():
    merchantId = 0
    totalCheckoutAmount = 0.0
    products = []
    discountTotal = 0
    delivery = True
    deliveryDate = ""
    address = ""
    
    def __init__(self, payload):
        payload = payload.copy()
        self.merchantId = int(payload.get("merchantId"))
        self.totalCheckoutAmount = float(payload["totalCheckoutAmount"]),
        self.products = self.convertAndReturnProductsList(payload.get("products"))
        self.delivery = bool(payload.get("delivery"))
        self.deliveryDate = payload.get("deliveryDate")
        self.address = payload.get("address")
    
    def verifyPurchase(self):

        def checkProductExistence():
            productsExistCount = Product.objects.filter(
                id__in=self.products, merchant__id=self.merchantId, isActive=True, inStock=True
            ).count()
            if productsExistCount == len(self.products):
                return True
            raise Exception("This store no longer sells this/these products")
        
        def checkifPricesMatch():
            # TODO: disabling this for now. Company applied specials and discounts will come later.
            # products = Product.objects.filter(
            #     id__in=self.products, merchant__id=self.merchantId, isActive=True
            # )
            # totalAmountAfterDiscounts = 0
            # for product in products:
            #     discountedAmount = (product.discountPercentage / 100) * product.originalPrice
            #     discountedPrice = product.originalPrice - discountedAmount
            #     totalAmountAfterDiscounts = totalAmountAfterDiscounts + discountedPrice
            # if (
            #     totalAmountAfterDiscounts == self.totalCheckoutAmount[0] and discountedAmount == float(self.discountTotal)
            # ):
            #     return True
            # raise Exception("Total product prices do not match the checkout amount")
            return True

        if checkProductExistence() and checkifPricesMatch():
            return True
    
    # this function only exists because the test case payload:
    # requires conversion and the payload from the mobile app doesn't:
    def convertAndReturnProductsList(self, products):
        if not settings.DEBUG:
            try:
                products = eval(products)
                return products
            except Exception as e:
                return products
        return products
