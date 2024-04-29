
from rest_framework import serializers
from apps.orders.models import Order
from apps.orders.serializers.ordered_product_serializer import OrderedProductSerializer


class OrderSerializer(serializers.ModelSerializer):

    class Meta:
        model = Order
        fields = "__all__"
        depth = 2

