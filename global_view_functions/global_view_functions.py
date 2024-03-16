

# functions shared by all views:

class GlobalViewFunctions():

    def checkIfUserHasFullPermissions(self, userAccount, exceptionString=""):
        if userAccount.user.is_superuser: 
            if userAccount.can_create_merchants: return True
            else: raise Exception(exceptionString)
        else: raise Exception(exceptionString)