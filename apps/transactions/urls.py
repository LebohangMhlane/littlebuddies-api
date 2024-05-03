
from django.urls import path

from apps.transactions.views import CheckTransactionStatusView

urlpatterns = [
    path('check-transaction-status/<str:reference>', CheckTransactionStatusView.as_view(), name="check_transaction_status"),
]

