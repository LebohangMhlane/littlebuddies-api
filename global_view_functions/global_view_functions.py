

# functions shared by all views:

from apps.merchants.models import Merchant


class GlobalViewFunctions():

    def checkIfUserIsSuperAdmin(self, request, exceptionString=None):
        if not request.user.is_superuser and not (
            request.user.useraccount.canCreateMerchants):
            raise Exception("Only super admins can perform this action" 
                if not exceptionString else exceptionString
            )
        return True
    
    def checkIfUserIsMerchantAdmin(self, request, exceptionString):
        if not request.user.useraccount.isMerchant:
            raise Exception("You don't have merchant authority to perform this action")

    def checkIfMerchantsMatch(self, request, merchantFromProduct):
        userAccount = request.user.useraccount
        merchant = Merchant.objects.get(userAccount=userAccount)
        if merchant == merchantFromProduct: 
            return True
        else: raise Exception("The product being deleted doesn't belong to this merchant")