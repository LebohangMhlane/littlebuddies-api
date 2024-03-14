
from rest_framework import serializers
from merchants.models import Merchant


class MerchantAccountSerializer(serializers.ModelSerializer):

    class Meta:
        model = Merchant
        fields = "__all__"