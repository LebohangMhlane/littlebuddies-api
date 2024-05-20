

# functions shared by all views:

import traceback

import hashlib
from apps.merchants.models import MerchantBusiness
from apps.products.models import Product
from apps.products.serializers.serializers import ProductSerializer
import logging

logger = logging.getLogger(__name__)

class GlobalViewFunctions():

    exceptionString1 = "You do not have permission to delete a product"

    exceptionString2 = "You don't have permission to update a merchant"

    exceptionString3 = "You don't have permission to create merchants"

    def verifyPayloadIntegrity(self, payload:dict, secret="secret"):
        cleanedPayload = payload.copy()
        checksum_to_compare = cleanedPayload["CHECKSUM"]
        del cleanedPayload["CHECKSUM"]
        values_as_string = "".join(list(cleanedPayload.values()))
        values_as_string += secret
        checksum = hashlib.md5(values_as_string.encode('utf-8')).hexdigest()
        cleanedPayload["CHECKSUM"] = checksum_to_compare
        if checksum_to_compare == checksum:
            return (True, cleanedPayload)   
        else:
            return (False, cleanedPayload)

    def getMerchant(self, merchantId) -> MerchantBusiness:
        merchant = MerchantBusiness.objects.get(id=merchantId)
        return merchant

    def checkIfUserIsSuperAdmin(self, request):
        if request.user.is_superuser and request.user.useraccount.canCreateMerchants:
            return True
        return False
    
    def checkIfUserIsMerchant(self, request):
        if request.user.useraccount.isMerchant: return True
        return False

    def checkIfUserMatchesMerchant(self, request):
        merchant = MerchantBusiness.objects.get(pk=request.data["merchantPk"])
        if merchant.userAccount == request.user.useraccount: return True
        else: return False

    def checkIfUserMatchesProductMerchant(self, request, productMerchant:MerchantBusiness):
        userAccount = request.user.useraccount
        if userAccount == productMerchant.userAccount: return True
        return False

    def notifyAllOfItemCreation(self, instance):
        pass

    def getProducts(self, merchant):
        logger.info("Getting updated stores near customer...")
        try:
            products = Product.objects.filter(
                isActive=True,
                merchant=merchant,
                inStock=True,
            )
            if products:
                serializer = ProductSerializer(products, many=True)
            return serializer.data
        except Exception as e:
            tb = traceback.format_exc()
            raise (f"{str(e)}{tb}")