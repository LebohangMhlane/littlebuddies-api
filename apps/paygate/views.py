import json
import datetime
import hashlib
from django.http import HttpResponse
import requests

from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from cryptography.fernet import Fernet as fernet

from apps.merchants.models import Merchant
from apps.paygate.app_models.app_models import CheckoutFormPayload
from apps.transactions.models import Transaction
from apps.transactions.serializers.transaction_serializer import TransactionSerializer
from global_view_functions.global_view_functions import GlobalViewFunctions

from global_test_config.global_test_config import GlobalTestCaseConfig


class PaymentInitializationView(APIView, GlobalViewFunctions, GlobalTestCaseConfig):

    permission_classes = [] # TODO: add later

    ngrok_base_url = "https://6628-41-10-121-222.ngrok-free.app/" # TODO: for development use only:

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return Response({
            "message_sent": True
        })

    def post(self, request, *args, **kwargs):
        try:
            checkoutFormData = CheckoutFormPayload(payload=request.data)
            merchant = self.getMerchant(checkoutFormData.merchantId)
            paygatePayload, reference = self.preparePayGatePayload(
                checkoutFormData, merchant, request
            )
            if checkoutFormData.verifyPurchase(checkoutFormData):
                response = self.sendInitiatePaymentRequestToPaygate(paygatePayload)
            if response.status_code == 200:
                responseData = response.text.split("&")
                responseAsDict = self.convertResponseToDict(responseData)
                dataIntegritySecure, verifiedPayload = self.verifyPayloadIntegrity(
                    responseAsDict, secret=merchant.getMerchantSecretKey()
                )
                if dataIntegritySecure:
                    transaction = self.createATransaction(
                        request, checkoutFormData, merchant, reference, verifiedPayload
                    )
                    if transaction:
                        transactionSerializer = TransactionSerializer(transaction, many=False)
                    return Response({
                        "success": True,
                        "message": "Paygate response was successful",
                        "paygatePayload": verifiedPayload,
                        "transaction": transactionSerializer.data
                    }, content_type='application/json', status=200)
                else:
                    raise Exception("Data integrity not secure")
            else:
                raise Exception(f"Response from Paygate was {response.status_code}")
        except Exception as e:
            return Response({
                "success": False,
                "message": "Failed to initialize Paygate payment",
                "error": str(e)},
                content_type='application/json', status=500)
    
    # prepare and return the payload we need to send to paygate to initiate a payment:
    def preparePayGatePayload(self, checkoutFormData, merchant:Merchant, request):
        reference = self.createReference(merchant, request)
        paygatePayload = {
            "PAYGATE_ID": merchant.paygateId,
            "REFERENCE": reference,
            "AMOUNT": checkoutFormData.totalCheckoutAmount,
            "CURRENCY": "ZAR",
            "RETURN_URL": f"{self.ngrok_base_url}/payment_notification/",
            "TRANSACTION_DATE": "2018-01-01 12:00:00",
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
    
    # TODO: we need to generate a reference for production:
    def createReference(self, merchant:Merchant, request):
        merchantTransactionCount = Transaction.objects.filter(merchant=merchant).count()
        reference = f"Transaction{merchant.id}{request.user.useraccount.phoneNumber}{request.user.pk}{merchantTransactionCount}"
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
        paygateInitiateUrl = "https://secure.paygate.co.za/payweb3/initiate.trans"
        response = requests.post(
            paygateInitiateUrl,
            data=paygatePayload
        )
        return response

    def createATransaction(
            self, request, checkoutFormData, merchant, reference, verifiedPayload
        ):
        productCount = len(checkoutFormData.products)
        def findDuplicateTransaction():
            return Transaction.objects.filter(
                payRequestId=verifiedPayload["PAY_REQUEST_ID"],
                reference=reference,
                customer=request.user.useraccount,
                merchant__id=checkoutFormData.merchantId,
                amount=checkoutFormData.totalCheckoutAmount,
                productsPurchased__id__in=checkoutFormData.products,
                numberOfProducts=productCount,
                discountTotal=checkoutFormData.discountTotal,
                completed=False
            ).exists()
        if not findDuplicateTransaction():
            transaction = Transaction.objects.create(
                payRequestId=verifiedPayload["PAY_REQUEST_ID"],
                reference=reference,
                customer=request.user.useraccount,
                merchant=merchant,
                amount=checkoutFormData.totalCheckoutAmount,
                numberOfProducts=productCount,
                completed=False,
                discountTotal=checkoutFormData.discountTotal,
                dateCreated=datetime.datetime.now(),
            )
            transaction.productsPurchased.set(checkoutFormData.products)
            transaction.save()
            return transaction
        else:
            transaction = Transaction.objects.filter(
                payRequestId=verifiedPayload["PAY_REQUEST_ID"],
                reference=reference,
                customer=request.user.useraccount,
                merchant__id=checkoutFormData.merchantId,
                amount=checkoutFormData.totalCheckoutAmount,
                productsPurchased__id__in=checkoutFormData.products,
                numberOfProducts=productCount,
                discountTotal=checkoutFormData.discountTotal,
                completed=False
            ).first()
            return transaction
        
class PaymentNotificationView(APIView, GlobalViewFunctions):

    permission_classes = []
    
    def get(self, request, *args):
        return render(
            request=request,
            template_name="payfast_templates/payment_notification_page.html"
        )

    def post(self, request, *args, **kwargs):
        try:
            updatedTransaction = self.verifyAndUpdateTransaction(request.data)
            if updatedTransaction.completed:
                settings.FIREBASE_INSTANCE.sendNotification(
                    updatedTransaction.merchant,
                    updatedTransaction.customer,
                    updatedTransaction.payRequestId
                )
            print(json.dumps(request.data, indent=4))
        except Exception as e:
            pass
        return HttpResponse("OK")
    
    def verifyAndUpdateTransaction(self, receivedPayload):
        def setTransactionStatus(transactionStatus, transaction:Transaction):
            if transactionStatus == 0:
                transaction.notDone = True
            elif transactionStatus == 1:
                    transaction.completed = True
            elif transactionStatus == 2:
                    transaction.declined = True
            elif transactionStatus == 3:
                    transaction.cancelled = True
            elif transactionStatus == 4:
                transaction.userCancelled = True
            elif transactionStatus == 5:
                transaction.receievedByPaygate = True
            elif transactionStatus == 7:
                transaction.settlementVoided = True
            return transaction
        payRequestId = receivedPayload["PAY_REQUEST_ID"]
        transaction = Transaction.objects.filter(payRequestId=payRequestId).first()
        try:
            dataIntegritySecure, validatedPayload = self.verifyPayloadIntegrity(
                receivedPayload, secret=transaction.merchant.getMerchantSecretKey()
            ) # TODO: investigate checksum check failure in this step:
            payRequestId = validatedPayload["PAY_REQUEST_ID"]
            transactionStatus = int(validatedPayload["TRANSACTION_STATUS"])
            transaction = setTransactionStatus(transactionStatus, transaction)
            transaction.save()
            return transaction
        except Exception as e:
            # we cannot return an error response to paygate in this view
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


