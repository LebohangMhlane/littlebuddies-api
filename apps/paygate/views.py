import json
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
from apps.paygate.app_models.app_models import CheckoutFormPayload


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
            checkoutFormPayload = CheckoutFormPayload(payload=request.data)
            merchant = checkoutFormPayload.getMerchant()
            paygatePayload = self.preparePayGatePayload(checkoutFormPayload, merchant)
            response = self.sendInitiatePaymentRequestToPaygate(paygatePayload)
            if response.status_code == 200:
                responseData = response.text.split("&")
                responseAsDict = self.convertResponseToDict(responseData)
                dataIntegritySecure, verifiedPayload = self.verifyPayloadIntegrity(
                    responseAsDict, secret=self.getMerchantSecretKey(merchant)
                )
                if dataIntegritySecure:
                    return Response({
                        "success": True,
                        "responseData": verifiedPayload,
                    }, content_type='application/json', status=200)
                else:
                    return Response({
                        "success": False, 
                        "responseData": {},
                        "error": "Data integrity violated!"
                    }, content_type='application/json', status=500)
            else:
                return Response({
                    "success": False, 
                    "responseData": {},
                    "error": f"Server error: {response.status_code}"
                }, content_type='application/json', status=500)
        except Exception as e:
            return Response({
                "success": False, 
                "responseData": {}, 
                "error": str(e)}, 
                content_type='application/json', status=500)
    
    # prepare and return the payload we need to send to paygate to initiate payment:
    def preparePayGatePayload(self, checkoutFormPayload, merchant):
        paygatePayload = {
            "PAYGATE_ID": merchant.paygateId,
            "REFERENCE": merchant.reference,
            "AMOUNT": checkoutFormPayload.totalCheckoutAmount,
            "CURRENCY": "ZAR",
            "RETURN_URL": "https://my.return.url/page",
            "TRANSACTION_DATE": "2018-01-01 12:00:00",
            "LOCALE": "en-za",
            "COUNTRY":"ZAF",
            "EMAIL": "customer@paygate.co.za",
        }
        merchantPaygateSecretKey = self.getMerchantSecretKey(merchant)
        if type(merchantPaygateSecretKey) is not Exception:
            paygatePayload["CHECKSUM"] = self.generateChecksum(
                paygate_data=paygatePayload, 
                merchantPaygateSecretKey=merchantPaygateSecretKey
            )   
            return paygatePayload
        else:
            return merchantPaygateSecretKey
        
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
            return Exception("Failed to decrypt token")

    def sendInitiatePaymentRequestToPaygate(self, paygatePayload):
        paygateInitiateUrl = "https://secure.paygate.co.za/payweb3/initiate.trans"
        response = requests.post(
            paygateInitiateUrl,
            data=paygatePayload
        )
        return response

    def sendProcessPaymentRequestToPaygate(self, request, paygateProcessPayload):
        del paygateProcessPayload["PAYGATE_ID"]
        del paygateProcessPayload["REFERENCE"]
        return Response(paygateProcessPayload)
        

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


