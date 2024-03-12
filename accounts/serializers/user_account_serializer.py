
from accounts.models import UserAccount
from rest_framework import serializers

from accounts.serializers.user_serializer import UserSerializer

class UserAccountSerializer(serializers.HyperlinkedModelSerializer):

    user = UserSerializer()

    class Meta:
        model = UserAccount
        fields = "__all__"