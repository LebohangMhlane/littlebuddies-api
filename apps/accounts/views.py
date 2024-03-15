from rest_framework.views import APIView
from rest_framework.response import Response

from apps.accounts.serializers.user_account_serializer import UserAccountSerializer
from apps.accounts.serializers.user_serializer import UserSerializer


class CreateAccountView(APIView):

    permission_classes = []

    def get(self, request, *args, **kwargs):
        pass

    def post(self, request, *args, **kwargs):
        try:
            self.createUser(receivedPayload=request.data)
            return Response({
                "success": True,
                "accountCreated": True,
            })
        except Exception as e:
            return Response({
                "success": False,
                "accountCreated": False,
                "exception": str(e)
            }, status=500)

    def createUser(self, receivedPayload=dict):
        userPayload, userAccountPayload = self.sortData(receivedPayload)
        userSerializer = UserSerializer(data=receivedPayload)
        if userSerializer.is_valid():
            userInstance = userSerializer.create(validated_data=userPayload)
            if userInstance:
                self.createUserAccount(userAccountPayload, userInstance)

    def sortData(self, receivedPayload):
        userPayload = {
            "username": receivedPayload["username"],
            "password": receivedPayload["password"],
            "firstName": receivedPayload["firstName"],
            "lastName": receivedPayload["lastName"],
            "email": receivedPayload["email"],
        }
        userAccountPayload = {
            "address": receivedPayload["address"],
            "phoneNumber": receivedPayload["phoneNumber"],
            "isMerchant": receivedPayload["isMerchant"],
        }
        return userPayload, userAccountPayload
    
    def createUserAccount(self, userAccountPayload, userInstance):
        userAccountPayload["user"] = userInstance
        userAccountSerializer = UserAccountSerializer(data=userAccountPayload)
        if userAccountSerializer.is_valid(raise_exception=True):
            userAccountSerializer.create(validated_data=userAccountPayload)