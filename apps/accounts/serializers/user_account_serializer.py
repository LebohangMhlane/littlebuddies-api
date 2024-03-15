
import re
from apps.accounts.models import UserAccount
from rest_framework import serializers

from global_serializer_functions.global_serializer_functions import (
    deleteAllUserRelatedInstances
)

class UserAccountSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserAccount
        fields = "__all__"

    def is_valid(self, *, raise_exception=True):
        initialData = self.initial_data
        if self.phoneNumberIsValid(initialData["phoneNumber"]):
            return True
        else:
            deleteAllUserRelatedInstances(initialData["user"].pk)
            raise Exception("User account phone number is invalid")
    
    def phoneNumberIsValid(self, phoneNumber):
        try:
            if not len(phoneNumber) == 10: return False
            pattern = r'0((60[3-9]|64[0-5]|66[0-5])\d{6}|(7[1-4689]|6[1-3]|8[1-4])\d{7})'
            if not re.match(pattern, phoneNumber): return False
            return True
        except Exception as e:
            return False

    def create(self, validated_data):
        try:
            userAccount = UserAccount()
            userAccount.user = validated_data["user"]
            userAccount.address = validated_data["address"]
            userAccount.phone_number = validated_data["phoneNumber"]
            userAccount.save()
            return userAccount
        except:
            deleteAllUserRelatedInstances(validated_data["user"].pk)
            raise Exception("Failed to create User Account")