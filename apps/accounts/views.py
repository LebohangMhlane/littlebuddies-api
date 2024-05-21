
from django.contrib.auth.models import User

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken

from apps.accounts.models import UserAccount
from apps.accounts.serializers.user_account_serializer import UserAccountSerializer
from apps.accounts.serializers.user_serializer import UserSerializer
from global_serializer_functions.global_serializer_functions import SerializerFunctions
from global_view_functions.global_view_functions import GlobalViewFunctions


class LoginView(ObtainAuthToken, GlobalViewFunctions):

    permission_classes = []

    def post(self, request, *args, **kwargs):
        try:
            user = User.objects.get(email=request.data["email"])
            if user.check_password(request.data["password"]):
                authToken = Token.objects.get(user=user)
                userAccount = UserAccount.objects.get(user=user)
                userAccountSerializer = UserAccountSerializer(userAccount, many=False)
            else:
                raise Exception("Invalid username or password")
            
            self._saveDeviceToken(user, request)
            
            return Response({
                "token": authToken.key,
                "userProfile": userAccountSerializer.data
            })
        except Exception as e:
            error = e.args[0]
            if("User matching query does not exist" in error):
                e = "No user with that email address was found"
            return Response({
                "message": "Failed to authenticate user",
                "error": str(e)
            }, status=401)
        
    def _saveDeviceToken(self, user, request):
        userAccount = UserAccount.objects.get(user=user)
        if "deviceToken" in request.data: # only for test cases:
            userAccount.deviceToken = request.data["deviceToken"]
        userAccount.save()

class RegistrationView(APIView, GlobalViewFunctions, SerializerFunctions):

    permission_classes = []

    def get(self, request, *args, **kwargs):
        pass
    
    def post(self, request, *args, **kwargs):

        userAccount = None

        try:
            userAccount = self._startRegistrationProcess(receivedData=request.data)
            authToken = Token.objects.get(user__id=userAccount.data["user"]["id"])

            self._sendVerificationEmail(userAccount, authToken)

            return Response({
                "message": "Account created successfully",
                "userAccount": userAccount.data,
                "loginToken": authToken.key
            })
        
        except Exception as e:

            error = ""

            if "UNIQUE" in str(e.args[0]):
                error = "A user with these details already exists"
            return Response({
                "message": "Failed to create account",
                "error": "An error has occured. We are looking into it"
            }, status=500)

    def _startRegistrationProcess(self, receivedData=dict):

        userData, userAccountData = self.sortData(receivedData)

        userSerializer = UserSerializer(data=receivedData)
        
        if userSerializer.is_valid():
            userInstance = userSerializer.create(validated_data=userData)
            if userInstance:
                userAccount = self.createUserAccount(userAccountData, userInstance)
                userAccount = UserAccountSerializer(userAccount, many=False)
                return userAccount

    def sortData(self, receivedPayload):
        userPayload = {
            "username": f"{receivedPayload['firstName']}{receivedPayload['lastName']}{receivedPayload['phoneNumber']}",
            "password": receivedPayload["password"],
            "firstName": receivedPayload["firstName"],
            "lastName": receivedPayload["lastName"],
            "email": receivedPayload["email"],
        }
        userAccountPayload = {
            "deviceToken": receivedPayload["deviceToken"] if "deviceToken" in receivedPayload else "",
            "phoneNumber": receivedPayload["phoneNumber"],
        }
        return userPayload, userAccountPayload
    
    def createUserAccount(self, userAccountPayload, userInstance):

        userAccountPayload["user"] = userInstance

        userAccountSerializer = UserAccountSerializer(data=userAccountPayload)
        
        if userAccountSerializer.is_valid(raise_exception=True):
            userAccount = userAccountSerializer.create(validated_data=userAccountPayload)
            return userAccount
        
    def _sendVerificationEmail(self, userAccount, authToken):
        pass

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
                "error": str(e)
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