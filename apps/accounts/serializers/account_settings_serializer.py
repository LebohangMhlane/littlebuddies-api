
from apps.accounts.models import AccountSetting
from rest_framework import serializers

from apps.accounts.serializers.user_account_serializer import UserAccountSerializer
from global_serializer_functions.global_serializer_functions import (
    SerializerFunctions,
)

class AccountSettingsSerializer(serializers.ModelSerializer, SerializerFunctions):

    class Meta:
        model = AccountSetting
        fields = "__all__"
        depth = 1

    user_account = UserAccountSerializer()
