import json
import datetime
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from cryptography.fernet import Fernet as fernet
import hashlib
import requests

from apps.merchants.models import Merchant
from apps.paygate.app_models.app_models import CheckoutFormData
from apps.transactions.models import Transaction
from apps.transactions.serializers.transaction_serializer import TransactionSerializer


class PaymentInitializationView(APIView):

    permission_classes = [IsAuthenticated]

    ngrok_base_url = "https://de99-41-10-117-107.ngrok-free.app" # TODO: for development use only:

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return Response({
            "message_sent": True
        })

    def post(self, request, *args, **kwargs):
        try:
            checkoutFormData = CheckoutFormData(payload=request.data)
            merchant = checkoutFormData.getMerchant()
            paygatePayload, reference = self.preparePayGatePayload(checkoutFormData, merchant, request)
            response = self.sendInitiatePaymentRequestToPaygate(paygatePayload)
            if response.status_code == 200:
                responseData = response.text.split("&")
                responseAsDict = self.convertResponseToDict(responseData)
                dataIntegritySecure, verifiedPayload = self.verifyPayloadIntegrity(
                    responseAsDict, secret=self.getMerchantSecretKey(merchant)
                )
                if dataIntegritySecure:
                    transaction = self.createATransaction(request, checkoutFormData, merchant, reference)
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
        reference = self.createReference(merchant, checkoutFormData, request)
        paygatePayload = {
            "PAYGATE_ID": merchant.paygateId,
            "REFERENCE": reference,
            "AMOUNT": checkoutFormData.totalCheckoutAmount,
            "CURRENCY": "ZAR",
            "RETURN_URL": "https://my.return.url/page",
            "TRANSACTION_DATE": "2018-01-01 12:00:00",
            "LOCALE": "en-za",
            "COUNTRY":"ZAF",
            "EMAIL": "customer@paygate.co.za",
        }
        merchantPaygateSecretKey = self.getMerchantSecretKey(merchant)
        paygatePayload["CHECKSUM"] = self.generateChecksum(
            paygate_data=paygatePayload, 
            merchantPaygateSecretKey=merchantPaygateSecretKey
        )   
        return paygatePayload, reference
        
        
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

    def verifyPayloadIntegrity(self, cleanedPayload:dict, secret="secret"):
        checksum_to_compare = cleanedPayload["CHECKSUM"]
        del cleanedPayload["CHECKSUM"]
        values_as_string = "".join(list(cleanedPayload.values()))
        values_as_string += secret
        checksum = hashlib.md5(values_as_string.encode('utf-8')).hexdigest()
        cleanedPayload["CHECKSUM"] = checksum_to_compare
        if checksum_to_compare == checksum:
            return (True, cleanedPayload)   
        else:
            return (False, cleanedPayload)

    def getMerchantSecretKey(self, merchant:Merchant):
        try:
            fernetToken = merchant.fernetToken.encode('utf-8')[2:-1]
            fernetInstance = fernet(key=settings.FERNET_KEY)
            secret = fernetInstance.decrypt(fernetToken).decode("utf-8")
            return secret
        except Exception as e:
            raise Exception(f"Failed to decrypt token: {str(e)}")

    def sendInitiatePaymentRequestToPaygate(self, paygatePayload):
        paygateInitiateUrl = "https://secure.paygate.co.za/payweb3/initiate.trans"
        response = requests.post(
            paygateInitiateUrl,
            data=paygatePayload
        )
        return response
    
    # TODO: generate your own reference for production environment
    def createReference(self, checkoutFormData, merchant, request):
        paygateTestReference = "pgtest_123456789"
        return paygateTestReference

    def createATransaction(self, request, checkoutFormData:CheckoutFormData, merchant, reference): 
        products = list(eval(checkoutFormData.products))
        productCount = len(list(eval(checkoutFormData.products)))
        def aDuplicateTransaction():
            return Transaction.objects.filter(
                customer=request.user.useraccount,
                merchant__id=checkoutFormData.merchantId,
                amount=checkoutFormData.totalCheckoutAmount,
                productsPurchased__id__in=products,
                numberOfProducts=productCount,
                discountTotal=checkoutFormData.discountTotal,
                completed=False
            ).exists()
        if not aDuplicateTransaction():
            transaction = Transaction.objects.create(
                reference=reference,
                customer=request.user.useraccount,
                merchant=merchant,
                amount=checkoutFormData.totalCheckoutAmount,
                numberOfProducts=productCount,
                completed=False,
                discountTotal=checkoutFormData.discountTotal,
                dateCreated=datetime.datetime.now(),
            )
            transaction.productsPurchased.set(products)
            transaction.save()
            return transaction
        else:
            transaction = Transaction.objects.get(
                customer=request.user.useraccount,
                merchant__id=checkoutFormData.merchantId,
                amount=checkoutFormData.totalCheckoutAmount,
                productsPurchased__id__in=products,
                numberOfProducts=productCount,
                discountTotal=checkoutFormData.discountTotal,
                completed=False
            )
            return transaction
        
class PaymentNotificationView(APIView):
    
    def get(self, request, *args):
        return render(
            request=request, 
            template_name="payfast_templates/payment_notification_page.html"
        )

    def post(self, request, *args, **kwargs):

        settings.FIREBASE_INSTANCE.sendNotification()

        print(json.dumps(request.data, indent=4))
        return Response({
            "notification_received": True,
        })

class PaymentSuccessView(APIView):

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


