from rest_framework.views import APIView
from rest_framework.response import Response

from apps.accounts.serializers.user_account_serializer import UserAccountSerializer
from apps.accounts.serializers.user_serializer import UserSerializer
from global_view_functions.global_view_functions import GlobalViewFunctions


class CreateAccountView(APIView, GlobalViewFunctions):

    permission_classes = []

    def get(self, request, *args, **kwargs):
        pass

    def post(self, request, *args, **kwargs):
        try:
            userAccount = self.createUser(receivedPayload=request.data)
            return Response({
                "success": True,
                "message": "Account created successfully",
                "userAccount": userAccount.data
            })
        except Exception as e:
            return Response({
                "success": False,
                "message": "Failed to create account",
                "exception": str(e)
            }, status=500)

    def createUser(self, receivedPayload=dict):
        userPayload, userAccountPayload = self.sortData(receivedPayload)
        userSerializer = UserSerializer(data=receivedPayload)
        if userSerializer.is_valid():
            userInstance = userSerializer.create(validated_data=userPayload)
            if userInstance:
                userAccount = self.createUserAccount(userAccountPayload, userInstance)
                userAccount = UserAccountSerializer(userAccount, many=False)
                return userAccount

    def sortData(self, receivedPayload):
        userPayload = {
            "username": receivedPayload["username"],
            "password": receivedPayload["password"],
            "firstName": receivedPayload["firstName"],
            "lastName": receivedPayload["lastName"],
            "email": receivedPayload["email"],
        }
        userAccountPayload = {
            "deviceToken": receivedPayload["deviceToken"],
            "address": receivedPayload["address"],
            "phoneNumber": receivedPayload["phoneNumber"],
            "isMerchant": receivedPayload["isMerchant"],
        }
        return userPayload, userAccountPayload
    
    def createUserAccount(self, userAccountPayload, userInstance):
        userAccountPayload["user"] = userInstance
        userAccountSerializer = UserAccountSerializer(data=userAccountPayload)
        if userAccountSerializer.is_valid(raise_exception=True):
            userAccount = userAccountSerializer.create(validated_data=userAccountPayload)
            return userAccount
        

class DeactivateAccountView(APIView, GlobalViewFunctions):

    def get(self, request):
        self.deactivateAccount(request)
        return Response({
            "success": True,
            "message": "Account deactivated successfully",
        }, status=200)
    
    def deactivateAccount(self, request):
        userAccount = request.user.useraccount
        user = request.user
        user.is_active = False
        user.save()
        userAccount.save()


class UpdateAccountView(APIView, GlobalViewFunctions):

    def post(self, request):
        try:
            updatedAccount = self.updateAccount(request)
            userAccountSerializer = UserAccountSerializer(updatedAccount, many=False)
            return Response({
                "success": True,
                "message": "Account updated successfully",
                "updatedAccount": userAccountSerializer.data
            }, status=200)
        except Exception as e:
            return Response({
                "success": False,
                "message": "Failed to update Account",
                "exception": str(e)
            }, status=500)
        
    def updateAccount(self, request):
        receivedPayload = request.data.copy()
        userAccount = request.user.useraccount
        for key, value in receivedPayload.items():
            self.validateKey(key, request)
            userAccount.__setattr__(key, value)
        userAccount.save()
        return userAccount
    
    def validateKey(self, key, request):
        if (key == "canCreateMerchants" or key == "isMerchant"):
            exceptionString = f"You don't have permission to modify {key}"
            self.checkIfUserIsSuperAdmin(request, exceptionString)
        
    def notifyAllOfUpdate(self):
        # send emails to relevant parties notifiying them of the deactivation:
        pass