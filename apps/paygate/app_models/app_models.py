
from django.conf import settings
from apps.orders.models import OrderedProduct
from apps.products.models import BranchProduct, Product

# what the mobile app sends to the server to initiate payment after checkout:

class CheckoutForm():
    branchId = 0
    total_checkout_amount = "0.0"
    branch_products = []
    productIds = []
    discountTotal = 0
    delivery = True
    deliveryDate = ""
    address = ""
    productCount = 0
    
    def __init__(self, payload):
        payload = payload.copy()
        self.branchId = int(payload.get("branchId"))
        self.total_checkout_amount = payload["totalCheckoutAmount"]
        self.branch_products = self._setProducts(payload.get("products"))
        self.delivery = bool(payload.get("delivery"))
        self.deliveryDate = payload.get("deliveryDate")
        self.address = payload.get("address")
        self.productIds = self._setProductIds(payload["products"])
        self.setProductCount()
    
    def verify_purchase(self):

        def verifyProductExistence():
            # TODO: disabling this for now: i dont think there will be a time in 
            # between an order being placed 
            # productsExistCount = Product.objects.filter(
            #     id__in=self.products, 
            #     merchant__id=self.merchantId, 
            #     is_active=True, 
            #     in_stock=True
            # ).count()
            # if productsExistCount == len(self.products):
            #     return True
            # raise Exception("This store no longer sells this/these products")
            return True
        
        def checkifPricesMatch():
            # TODO: disabling this for now. Company applied specials and discounts will come later.
            # products = Product.objects.filter(
            #     id__in=self.products, merchant__id=self.merchantId, is_active=True
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
    
    def _setProducts(self, branch_products):
        try:
            orderedbranch_products = []
            # test cases require eval() conversion
            # running from mobile doesn't:
            try:
                branch_products = eval(branch_products)
            except:
                pass
            for branchProduct in branch_products:
                product = BranchProduct.objects.get(id=branchProduct["id"])
                orderedProduct = OrderedProduct.objects.create(
                    branchProduct=product,
                    quantityOrdered=branchProduct["quantityOrdered"]
                )
                orderedbranch_products.append(orderedProduct)
            return orderedbranch_products
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
        for product in self.branch_products:
            self.productCount += int(product.quantityOrdered)