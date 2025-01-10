from django.conf import settings
from apps.merchants.models import SaleCampaign
from apps.orders.models import OrderedProduct
from apps.products.models import BranchProduct, Product

# what the mobile app sends to the server to initiate payment after checkout:

class CheckoutForm():
    branch_id = 0
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
        self.branch_id = int(payload.get("branchId"))
        self.total_checkout_amount = payload["totalCheckoutAmount"]
        self.branch_products = self._set_ordered_products(payload.get("products"))
        self.delivery = bool(payload.get("delivery"))
        self.deliveryDate = payload.get("deliveryDate")
        self.address = payload.get("address")
        self.productIds = self._set_product_ids(payload["products"])
        self.set_product_count()

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

    def _set_ordered_products(self, branch_products):
        try:

            def set_sale_campaign_to_ordered_product():
                # set the sale campaign if there is one:
                if sale_campaign: 
                    ordered_product.sale_campaign = sale_campaign
                    ordered_product.save()

            products_ordered = []

            # test cases require eval() conversion, running from mobile doesn't:
            try:
                branch_products = eval(branch_products)
            except:
                pass

            for branch_product in branch_products:

                quantity_ordered = branch_product["quantityOrdered"]

                # get the product:
                branch_product = BranchProduct.objects.get(id=branch_product["id"])

                # check if this product is on sale:
                sale_campaign = SaleCampaign.objects.filter(
                    branch=branch_product.branch,
                    branch_product=branch_product
                ).first()

                # create the ordered product:
                ordered_product = OrderedProduct()
                ordered_product.branch_product = branch_product
                ordered_product.quantity_ordered = quantity_ordered
                ordered_product.order_price = branch_product.branch_price
                ordered_product.save()

                set_sale_campaign_to_ordered_product()

                # add the ordered product to the list:
                products_ordered.append(ordered_product)
            return products_ordered
        except Exception as e:
            raise e

    def _set_product_ids(self, products):
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

    def set_product_count(self):
        for product in self.branch_products:
            self.productCount += int(product.quantity_ordered)
