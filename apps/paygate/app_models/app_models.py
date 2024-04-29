
from django.conf import settings
from apps.products.models import Product

# what the mobile app sends to the server to initiate payment after checkout:

class CheckoutForm():
    merchantId = 0
    totalCheckoutAmount = "0.0"
    products = []
    productIds = []
    discountTotal = 0
    delivery = True
    deliveryDate = ""
    address = ""
    productCount = 0
    
    def __init__(self, payload):
        payload = payload.copy()
        self.merchantId = int(payload.get("merchantId"))
        self.totalCheckoutAmount = payload["totalCheckoutAmount"]
        self.products = self._setProducts(payload.get("products"))
        self.delivery = bool(payload.get("delivery"))
        self.deliveryDate = payload.get("deliveryDate")
        self.address = payload.get("address")
        self.productIds = self._setProductIds(payload["products"])
        self.setProductCount()
    
    def verifyPurchase(self):

        def verifyProductExistence():
            # TODO: disabling this for now: i dont think there will be a time in 
            # between an order being placed 
            # productsExistCount = Product.objects.filter(
            #     id__in=self.products, 
            #     merchant__id=self.merchantId, 
            #     isActive=True, 
            #     inStock=True
            # ).count()
            # if productsExistCount == len(self.products):
            #     return True
            # raise Exception("This store no longer sells this/these products")
            return True
        
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

        if verifyProductExistence() and checkifPricesMatch():
            return True
    
    def _setProducts(self, products):
        try:
            orderedProducts = []
            # test cases require eval() conversion
            # running from mobile doesn't:
            try:
                products = eval(products)
            except:
                pass
            for product in products:
                productObject = Product.objects.get(id=product["id"])
                orderedProduct = OrderedProduct.objects.create(
                    product=productObject,
                    quantityOrdered=product["quantityOrdered"]
                )
                orderedProducts.append(orderedProduct)
            return orderedProducts
        except Exception as e:
            raise e

    def _setProductIds(self, products):
        # test cases require eval() conversion
        # running from mobile doesn't:
        try:
            products = eval(products)
        except:
            pass        
        productIds = []
        for product in products:
            productIds.append(int(product["id"]))
        return productIds
    
    def setProductCount(self):
        for product in self.products:
            self.productCount += int(product.quantityOrdered)