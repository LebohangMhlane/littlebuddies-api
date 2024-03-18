

# functions shared by all views:

from apps.accounts.models import UserAccount
from apps.merchants.models import Merchant


class GlobalViewFunctions():

    def checkIfUserHasFullPermissions(self, request, exceptionString=""):
        userAccount = UserAccount.objects.get(pk=request.user.useraccount.pk)
        if userAccount.user.is_superuser: 
            if userAccount.can_create_merchants: return True
            else: raise Exception(exceptionString)
        else: raise Exception(exceptionString)

    def checkIfUserBelongsToMerchant(self, request, exceptionString):
        merchant = Merchant.objects.get(pk=request.data["merchantPk"])
        if merchant.user_account == request.user.useraccount:
            return True
        else: return False