
import re
from apps.accounts.models import UserAccount
from rest_framework import serializers

from apps.accounts.serializers.user_serializer import UserSerializer
from global_serializer_functions.global_serializer_functions import (
    SerializerFunctions,
)

class UserAccountSerializer(serializers.ModelSerializer, SerializerFunctions):

    class Meta:
        model = UserAccount
        fields = "__all__"
        depth = 1

    user = UserSerializer()
    
    def is_valid(self, *, raise_exception=True):
        initialData = self.initial_data
        if self.checkIfPhoneNumberIsValid(initialData["phoneNumber"]): return True
        else:
            self.deleteAllUserRelatedInstances(initialData["user"].pk)
            raise Exception("Invalid phone number")
    
    def create(self, validated_data):
        try:
            userAccount = UserAccount.objects.create(
                user = validated_data["user"],
                phoneNumber = validated_data["phoneNumber"],
                isMerchant = validated_data["isMerchant"],
                deviceToken = validated_data["deviceToken"],
            )
            return userAccount
        except Exception as e:
            self.deleteAllUserRelatedInstances(validated_data["user"].pk)
            raise Exception(f"Failed to create User Account {str(e)}")

    def checkIfPhoneNumberIsValid(self, phoneNumber):
        if not len(phoneNumber) == 10: return False
        pattern = r'0((60[3-9]|64[0-5]|66[0-5])\d{6}|(7[1-4689]|6[1-3]|8[1-4])\d{7})'
        if not re.match(pattern, phoneNumber): return False
        return True
