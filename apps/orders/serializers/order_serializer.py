
from rest_framework import serializers
from apps.orders.models import Order
from apps.products.serializers.serializers import ProductSerializer


class OrderSerializer(serializers.ModelSerializer):

    orderedProducts = ProductSerializer()
    class Meta:
        model = Order
        fields = "__all__"
        depth = 2

