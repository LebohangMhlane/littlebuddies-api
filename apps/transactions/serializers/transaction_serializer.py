
from rest_framework import serializers
from apps.merchants.models import Merchant
from apps.accounts.models import UserAccount
from apps.transactions.models import Transaction


class TransactionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Transaction
        fields = "__all__"
        depth = 2
