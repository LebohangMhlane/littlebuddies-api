
from rest_framework import serializers
from apps.orders.models import OrderedProduct


class OrderedProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrderedProduct
        fields = "__all__"
        depth = 3

