

from rest_framework import serializers
from apps.transactions.models import Order
from apps.transactions.serializers.transaction_serializer import TransactionSerializer


class OrderSerializer(serializers.ModelSerializer):

    transaction = TransactionSerializer()

    class Meta:
        model = Order
        fields = "__all__"
        depth = 2
