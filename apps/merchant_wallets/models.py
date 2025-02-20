from decimal import Decimal
from django.db import models

from apps.merchants.models import MerchantBusiness
from apps.transactions.models import Transaction
from apps.transactions.serializers.transaction_serializer import TransactionSerializer


class MerchantWallet(models.Model):
    merchant_business = models.ForeignKey('merchants.MerchantBusiness', on_delete=models.CASCADE)
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    transactions = models.ManyToManyField(to='transactions.Transaction', blank=True)

    def __str__(self):
        return f"{self.merchant_business.name} - {self.wallet_balance}"

    def get_all_transactions(self):
        transaction_serializer = TransactionSerializer(self.transactions, many=True)
        return transaction_serializer.data

    def get_balance(self):
        return str(self.wallet_balance)

    def update_balance(self, transaction:Transaction):
        if transaction.status == "COMPLETED":
            self.wallet_balance += Decimal(transaction.amount_minus_service_fee)
