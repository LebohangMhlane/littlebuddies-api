import json
import datetime
import hashlib
import requests

from django.http import HttpResponse
from django.conf import settings
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.integrations.firebase_integration.firebase_module import FirebaseInstance
from apps.merchants.models import Branch
from apps.orders.models import Order
from apps.orders.serializers.order_serializer import OrderSerializer
from apps.paygate.app_models.app_models import CheckoutForm
from apps.transactions.models import Transaction
from apps.transactions.serializers.transaction_serializer import TransactionSerializer

from global_view_functions.global_view_functions import GlobalViewFunctions

from global_test_config.global_test_config import GlobalTestCaseConfig

class PaymentInitializationView(APIView, GlobalViewFunctions, GlobalTestCaseConfig):

    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            checkoutForm = CheckoutForm(payload=request.data)
            branch = self.getBranch(checkoutForm.branchId)
            if checkoutForm.verifyPurchase():
                paygatePayload, reference = self.preparePayGatePayload(checkoutForm, branch, request)
                paygateResponse = self.sendInitiatePaymentRequestToPaygate(paygatePayload)
                
                if paygateResponse.status_code == 200:
                    responseAsDict = self.convertResponseToDict(paygateResponse.text.split("&"))
                    dataIntegritySecure, verifiedPayload = self.verifyPayloadIntegrity(
                        responseAsDict, secret=branch.merchant.getMerchantSecretKey()
                    )
                    
                    if dataIntegritySecure:
                        transaction = self.createATransaction(request, checkoutForm, branch, reference, verifiedPayload)
                        if transaction:
                            order = self.createAnOrder(transaction, checkoutForm)
                            return self.successResponse(verifiedPayload, transaction, order)
                        else:
                            raise Exception("Transaction creation failed")
                    else:
                        raise Exception("Data integrity not secure")
                else:
                    raise Exception(f"Response from Paygate was {paygateResponse.status_code}")
        except Exception as e:
            return self.errorResponse(str(e))

    def preparePayGatePayload(self, checkoutFormPayload: CheckoutForm, branch: Branch, request):
        reference = self.createReference(branch, request)
        totalCheckoutAmount = checkoutFormPayload.totalCheckoutAmount.replace(".", "") # paygate doesn't use decimals
        paygatePayload = {
            "PAYGATE_ID": branch.merchant.paygateId,
            "REFERENCE": reference,
            "AMOUNT": f"{totalCheckoutAmount}", 
            "CURRENCY": "ZAR",
            "RETURN_URL": f"{settings.SERVER_URL}/payment_notification/",
            "TRANSACTION_DATE": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "LOCALE": "en-za",
            "COUNTRY": "ZAF",
            "EMAIL": branch.merchant.userAccount.user.email,
        }
        paygatePayload["CHECKSUM"] = self.generateChecksum(paygatePayload, branch.merchant.getMerchantSecretKey())
        return paygatePayload, reference

    def createReference(self, branch: Branch, request):
        numOfBranchTransactions = Transaction.objects.filter(branch=branch).count()
        reference = f"T{branch.id}{str(request.user.useraccount.phoneNumber)[-4:]}{request.user.pk}{numOfBranchTransactions}"
        return reference

    def generateChecksum(self, paygate_data, merchantPaygateSecretKey=""):
        payload = "".join(str(value) for value in paygate_data.values())
        if merchantPaygateSecretKey:
            payload += merchantPaygateSecretKey
        return hashlib.md5(payload.encode("utf-8")).hexdigest()

    def convertResponseToDict(self, response_data):
        return dict(data_piece.split("=") for data_piece in response_data)

    def sendInitiatePaymentRequestToPaygate(self, paygatePayload):
        return requests.post(settings.PAYGATE_INITIATE_PAYMENT_URL, data=paygatePayload)

    def createATransaction(self, request, checkoutFormPayload: CheckoutForm, branch: Branch, reference, verifiedPayload):
        if not Transaction.objects.filter(
            payRequestId=verifiedPayload["PAY_REQUEST_ID"],
            reference=reference,
            customer=request.user.useraccount,
            branch=branch,
            amount=checkoutFormPayload.totalCheckoutAmount,
            productsPurchased__id__in=checkoutFormPayload.productIds,
            numberOfProducts=checkoutFormPayload.productCount,
            discountTotal=checkoutFormPayload.discountTotal,
            status=Transaction.PENDING,
        ).exists():
            transaction = Transaction.objects.create(
                payRequestId=verifiedPayload["PAY_REQUEST_ID"],
                reference=reference,
                customer=request.user.useraccount,
                branch=branch,
                amount=checkoutFormPayload.totalCheckoutAmount,
                numberOfProducts=checkoutFormPayload.productCount,
                status=Transaction.PENDING,
                discountTotal=checkoutFormPayload.discountTotal,
                dateCreated=datetime.datetime.now(),
            )
            transaction.productsPurchased.set(checkoutFormPayload.branchProducts)
            transaction.save()
            return transaction
        return Transaction.objects.filter(
            payRequestId=verifiedPayload["PAY_REQUEST_ID"],
            reference=reference,
            customer=request.user.useraccount,
            branch=branch,
            amount=str(checkoutFormPayload.totalCheckoutAmount),
            productsPurchased__id__in=checkoutFormPayload.branchProducts,
            numberOfProducts=checkoutFormPayload.productCount,
            discountTotal=checkoutFormPayload.discountTotal,
            status=Transaction.PENDING,
        ).first()

    def createAnOrder(self, transaction: Transaction, checkoutForm: CheckoutForm):
        try:
            order = Order.objects.create(
                transaction=transaction,
                status=Order.PENDING_DELIVERY,
                delivery=checkoutForm.delivery,
                deliveryDate=checkoutForm.deliveryDate,
                address=checkoutForm.address,
            )
            order.orderedProducts.add(*transaction.productsPurchased.all())
            order.save()
            for orderedProduct in transaction.productsPurchased.all():
                orderedProduct.order = order
                orderedProduct.save()
            return order
        except Exception as e:
            raise Exception("Failed to create order")

    def successResponse(self, verifiedPayload, transaction, order):
        orderSerializer = OrderSerializer(order, many=False)
        transactionSerializer = TransactionSerializer(transaction, many=False)
        return Response(
            {
                "success": True,
                "message": "Paygate response was successful",
                "paygatePayload": verifiedPayload,
                "transaction": transactionSerializer.data,
                "order": orderSerializer.data,
            },
            content_type="application/json",
            status=200,
        )

    def errorResponse(self, error_message):
        return Response(
            {
                "success": False,
                "message": "Failed to initialize Paygate payment",
                "error": error_message,
            },
            content_type="application/json",
            status=500,
        )



class PaymentNotificationView(APIView, GlobalViewFunctions):

    permission_classes = []

    def post(self, request, *args, **kwargs):
        try:
            updatedTransaction = self.verifyAndUpdateTransactionStatus(request.data)
            if updatedTransaction.status == updatedTransaction.COMPLETED:
                order = self.updateOrder(updatedTransaction)
                _ = FirebaseInstance().sendTransactionStatusNotification(
                    updatedTransaction
                )
                self.sendOrderEmail(updatedTransaction, order)
        except Exception as e:
            pass
        return HttpResponse("OK")

    def verifyAndUpdateTransactionStatus(self, receivedPayload):
        def setTransactionStatus(transactionStatus, transaction: Transaction):
            if transactionStatus == 0:
                transaction.status = Transaction.NOT_DONE
            elif transactionStatus == 1:
                transaction.status = Transaction.COMPLETED
            elif transactionStatus == 2:
                transaction.status = Transaction.DECLINED
            elif transactionStatus == 3:
                transaction.status = Transaction.CANCELLED
            elif transactionStatus == 4:
                transaction.status = Transaction.CUSTOMER_CANCELLED
            elif transactionStatus == 5:
                transaction.status = Transaction.RECEIVED_BY_PAYGATE
            elif transactionStatus == 7:
                transaction.status = Transaction.SETTLEMENT_VOIDED
            return transaction

        try:
            payRequestId = receivedPayload["PAY_REQUEST_ID"]
            transaction = Transaction.objects.filter(payRequestId=payRequestId).first()
            dataIntegritySecure, validatedPayload = self.verifyPayloadIntegrity(
                receivedPayload,
                secret=transaction.branch.merchant.getMerchantSecretKey(),
            )  # TODO: investigate checksum check failure in this step:
            transactionStatus = int(validatedPayload["TRANSACTION_STATUS"])
            transaction = setTransactionStatus(transactionStatus, transaction)
            transaction.save()
            return transaction
        except Exception as e:
            # we cannot return an error response to paygate in this view
            pass

    def updateOrder(self, transaction):
        order = Order.objects.filter(transaction=transaction).first()
        if order:
            order.status = order.PENDING_DELIVERY
            order.save()
            return order
        return None

    def sendOrderEmail(self, updatedTransaction, order):
        pass


class PaymentSuccessView(APIView):

    permission_classes = []

    def get(self, request, *args, **kwargs):
        return render(
            request=request,
            template_name="payfast_templates/payment_successful_page.html",
            context={},
        )


class PaymentCancelledView(APIView):

    http_method_names = ["GET"]

    def get(self, request, *args):
        return Response(
            {
                "cancellation_received": True,
            }
        )
