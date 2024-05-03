
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.transactions.models import Transaction
from global_view_functions.global_view_functions import GlobalViewFunctions


class CheckTransactionStatusView(APIView, GlobalViewFunctions):
    
    def get(self, request, *args, **kwargs):
        try:
            reference = kwargs["reference"]
            transaction = Transaction.objects.get(reference=reference)
            transactionStatus = transaction.status
            return Response({
                "message": f"Transaction {reference} status retrieved successfully",
                "transactionStatus": transactionStatus
            })
        except Exception as e:
            return Response({
                "message": f"Failed to retrieve transaction {reference} status",
                "reason": str(e)
            })