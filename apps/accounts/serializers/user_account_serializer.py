
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
        if self.check_if_phone_number_is_valid(initialData["phoneNumber"]): return True
        else:
            self.delete_all_user_related_instances(initialData["user"].pk)
            raise Exception("Invalid phone number")
    
    def create(self, validated_data):
        try:
            userAccount = UserAccount.objects.create(
                user = validated_data["user"],
                phone_number = validated_data["phoneNumber"],
                device_token = validated_data["deviceToken"],
            )
            return userAccount
        except Exception as e:
            self.delete_all_user_related_instances(validated_data["user"].pk)
            raise Exception(f"Failed to create User Account {str(e)}")

    def check_if_phone_number_is_valid(self, phoneNumber):
        if not len(phoneNumber) == 10: return False
        pattern = r'0((60[3-9]|64[0-5]|66[0-5])\d{6}|(7[1-4689]|6[1-3]|8[1-4])\d{7})'
        if not re.match(pattern, phoneNumber): return False
        return True

class AddressUpdateSerializer(serializers.ModelSerializer):
    address = serializers.CharField(
        required=True,
        min_length=1,  
        error_messages={
            'required': 'Address field is required.',
            'blank': 'Address cannot be blank.',
            'min_length': 'Address cannot be empty.'
        }
    )

    class Meta:
        model = UserAccount
        fields = ['address']

    def validate_address(self, value):
        """
        Validate the address field.
        """
        if not value.strip(): 
            raise serializers.ValidationError("Address cannot be blank or just whitespace.")
        return value.strip()