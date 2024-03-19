

# functions shared by all views:

from apps.merchants.models import Merchant


class GlobalViewFunctions():

    exceptionString1 = "You do not have permission to delete a product"

    exceptionString2 = "You don't have permission to update a merchant"

    exceptionString3 = "You don't have permission to create merchants"

    def checkIfUserIsSuperAdmin(self, request):
        if request.user.is_superuser and request.user.useraccount.canCreateMerchants:
            return True
        return False
    
    def checkIfUserIsMerchant(self, request):
        if request.user.useraccount.isMerchant: return True
        return False

    def checkIfUserMatchesMerchant(self, request):
        merchant = Merchant.objects.get(pk=request.data["merchantPk"])
        if merchant.userAccount == request.user.useraccount: return True
        else: return False

    def checkIfUserMatchesProductMerchant(self, request, productMerchant:Merchant):
        userAccount = request.user.useraccount
        if userAccount == productMerchant.userAccount: return True
        return False

    def notifyAllOfItemCreation(self, instance):
        pass