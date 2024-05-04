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
from apps.merchants.models import MerchantBusiness
from apps.orders.models import Order
from apps.orders.serializers.order_serializer import OrderSerializer
from apps.paygate.app_models.app_models import CheckoutForm
from apps.transactions.models import Transaction
from apps.transactions.serializers.transaction_serializer import TransactionSerializer

from global_view_functions.global_view_functions import GlobalViewFunctions

from global_test_config.global_test_config import GlobalTestCaseConfig


class PaymentInitializationView(APIView, GlobalViewFunctions, GlobalTestCaseConfig):

    permission_classes = [IsAuthenticated] 

    ngrok_base_url = "https://b38c-41-10-119-195.ngrok-free.app" # TODO: for development use only:

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            checkoutForm = CheckoutForm(payload=request.data)
            merchant = self.getMerchant(checkoutForm.merchantId)
            if checkoutForm.verifyPurchase():
                paygatePayload, reference = self.preparePayGatePayload(
                    checkoutForm, merchant, request
                )
                paygateResponse = self.sendInitiatePaymentRequestToPaygate(paygatePayload)
            if paygateResponse.status_code == 200:
                responseData = paygateResponse.text.split("&")
                responseAsDict = self.convertResponseToDict(responseData)
                dataIntegritySecure, verifiedPayload = self.verifyPayloadIntegrity(
                    responseAsDict, secret=merchant.getMerchantSecretKey()
                )
                if dataIntegritySecure:
                    transaction = self.createATransaction(
                        request, checkoutForm, merchant, reference, verifiedPayload
                    )
                    if transaction:
                        order = self.createAnOrder(transaction, checkoutForm)
                        orderSerializer = OrderSerializer(order, many=False)
                        transactionSerializer = TransactionSerializer(transaction, many=False)
                    return Response({
                        "success": True,
                        "message": "Paygate response was successful",
                        "paygatePayload": verifiedPayload,
                        "transaction": transactionSerializer.data,
                        "order": orderSerializer.data
                    }, content_type='application/json', status=200)
                else:
                    raise Exception("Data integrity not secure")
            else:
                raise Exception(f"Response from Paygate was {paygateResponse.status_code}")
        except Exception as e:
            return Response({
                "success": False,   
                "message": "Failed to initialize Paygate payment",
                "error": str(e)},
                content_type='application/json', status=500)
    
    # prepare and return the payload we need to send to paygate to initiate a payment:
    # refer to docs: https://docs.paygate.co.za/?php#initiate
    def preparePayGatePayload(self, checkoutFormPayload:CheckoutForm, merchant:MerchantBusiness, request):
        reference = self.createReference(merchant, request)
        totalCheckoutAmount = checkoutFormPayload.totalCheckoutAmount.replace('.', '')
        paygatePayload = {
            "PAYGATE_ID": merchant.paygateId,
            "REFERENCE": reference,
            "AMOUNT": f"{totalCheckoutAmount}", # paygate doesn't use decimals
            "CURRENCY": "ZAR",
            "RETURN_URL": f"{settings.SERVER_URL}/payment_notification/",
            "TRANSACTION_DATE": "2018-01-01 12:00:00", # TODO: implement real time date
            "LOCALE": "en-za",
            "COUNTRY":"ZAF",
            "EMAIL": merchant.userAccount.user.email,
        }
        merchantPaygateSecretKey = merchant.getMerchantSecretKey()
        paygatePayload["CHECKSUM"] = self.generateChecksum(
            paygate_data=paygatePayload, 
            merchantPaygateSecretKey=merchantPaygateSecretKey
        )   
        return paygatePayload, reference
    
    def createReference(self, merchant:MerchantBusiness, request):
        merchantTransactionCount = Transaction.objects.filter(merchant=merchant).count()
        reference = f"T{merchant.id}{str(request.user.useraccount.phoneNumber)[-4:]}{request.user.pk}{merchantTransactionCount}"
        return reference
        
    def generateChecksum(self, paygate_data, merchantPaygateSecretKey = ''):
        checksum = ""
        payload = ""
        for key, value in paygate_data.items():
            payload += str(value) 
        if merchantPaygateSecretKey != '':
            payload += f"{merchantPaygateSecretKey}"
            checksum = hashlib.md5(payload.encode('utf-8')).hexdigest()
        return checksum

    def convertResponseToDict(self, response_data):
        convertedResponse = {}
        for data_piece in response_data:
            split_data = data_piece.split("=")
            convertedResponse[split_data[0]] = split_data[1]
        return convertedResponse

    def sendInitiatePaymentRequestToPaygate(self, paygatePayload):
        paygateInitiateUrl = settings.PAYGATE_INITIATE_PAYMENT_URL
        response = requests.post(
            paygateInitiateUrl,
            data=paygatePayload
        )
        return response

    def createATransaction(
            self, request, checkoutFormPayload:CheckoutForm, merchant, reference, verifiedPayload
        ):
        def findDuplicateTransaction():
            return Transaction.objects.filter(
                payRequestId=verifiedPayload["PAY_REQUEST_ID"],
                reference=reference,
                customer=request.user.useraccount,
                merchant__id=checkoutFormPayload.merchantId,
                amount=checkoutFormPayload.totalCheckoutAmount[0],
                productsPurchased__id__in=checkoutFormPayload.productIds,
                numberOfProducts=checkoutFormPayload.productCount,
                discountTotal=checkoutFormPayload.discountTotal,
                status=Transaction.PENDING
            ).exists()
        if not findDuplicateTransaction():
            transaction = Transaction.objects.create(
                payRequestId=verifiedPayload["PAY_REQUEST_ID"],
                reference=reference,
                customer=request.user.useraccount,
                merchant=merchant,
                amount=checkoutFormPayload.totalCheckoutAmount,
                numberOfProducts=checkoutFormPayload.productCount,
                status=Transaction.PENDING,
                discountTotal=checkoutFormPayload.discountTotal,
                dateCreated=datetime.datetime.now(),
            )
            transaction.productsPurchased.set(checkoutFormPayload.products)
            transaction.save()
            return transaction
        else:
            transaction = Transaction.objects.filter(
                payRequestId=verifiedPayload["PAY_REQUEST_ID"],
                reference=reference,
                customer=request.user.useraccount,
                merchant__id=checkoutFormPayload.merchantId,
                amount=str(checkoutFormPayload.totalCheckoutAmount),
                productsPurchased__id__in=checkoutFormPayload.products,
                numberOfProducts=checkoutFormPayload.productCount,
                discountTotal=checkoutFormPayload.discountTotal,
                status=Transaction.PENDING
            ).first()
            return transaction

    def createAnOrder(self, transaction:Transaction, checkoutForm:CheckoutForm):
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
                self.sendOrderEmails(updatedTransaction, order)
            print(json.dumps(request.data, indent=4))
        except Exception as e:
            pass
        return HttpResponse("OK")
    
    def verifyAndUpdateTransactionStatus(self, receivedPayload):
        def setTransactionStatus(transactionStatus, transaction:Transaction):
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
                receivedPayload, secret=transaction.merchant.getMerchantSecretKey()
            ) # TODO: investigate checksum check failure in this step:
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

    def sendOrderEmails(self, updatedTransaction, order):
        pass

class PaymentSuccessView(APIView):

    permission_classes = []

    def get(self, request, *args, **kwargs):
        return render(
            request=request, 
            template_name="payfast_templates/payment_successful_page.html",
            context={}
        )

class PaymentCancelledView(APIView):

    http_method_names = ["GET"]
    
    def get(self, request, *args):
        return Response({
            "cancellation_received": True,
        })


