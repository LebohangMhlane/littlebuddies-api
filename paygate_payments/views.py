import json
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import hashlib
import requests


class PaymentInitializationView(APIView):

    permission_classes = [] # add later

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
            paygate_data = self.getPayGateData(request=request)
            paygate_url = "https://secure.paygate.co.za/payweb3/initiate.trans"
            response = requests.post(
                paygate_url,
                data=paygate_data
            )
            if response.status_code == 200:
                response_data = response.text.split("&")
                cleaned_response_data = self.cleanResponseData(response_data)
                data_integrity_secure = self.verifyDataIntegrity(
                    cleaned_response_data, secret=self.getMerchantEncryptionKey()
                )
                if data_integrity_secure:
                    return Response({
                        "success": True, 
                        "responseData": cleaned_response_data
                    }, content_type='application/json')
                else:
                    return Response({
                        "success": False, 
                        "responseData": {},
                        "error": "Data integrity violated!"
                    }, content_type='application/json')
            else:
                return Response({
                    "success": False, 
                    "responseData": {},
                    "error": "Server error"
                }, content_type='application/json')
        except Exception as e:
            return Response({"success": False, "responseData": {}, "error": str(e)}, content_type='application/json')
    
    def getPayGateData(self, request):
        paygate_data = {
            "PAYGATE_ID": 10011072130,
            "REFERENCE": "pgtest_123456789",
            "AMOUNT": 3299,
            "CURRENCY": "ZAR",
            "RETURN_URL": "https://my.return.url/page",
            # "RETURN_URL": f"{settings.SERVER_URL}/payment_successful/",
            # "NOTIFY_URL": f"{settings.SERVER_URL}/payment_notification/",
            "TRANSACTION_DATE": "2018-01-01 12:00:00",
            "LOCALE": "en-za",
            "COUNTRY":"ZAF",
            "EMAIL": "customer@paygate.co.za",
            # "PAY_METHOD": "",
            # "PAY_METHOD_DETAIL": "",
            # "USER1": "",
            # "USER2": "",
            # "USER3": "",
            # "VAULT": "",
            # "VAULT_ID": "",
            # "VAULT_ID": "",
        }
        encryption_key = self.getMerchantEncryptionKey()
        paygate_data["CHECKSUM"] = self.generateChecksum(
            paygate_data=paygate_data, encryption_key=encryption_key
        )
        return paygate_data

    def generateChecksum(self, paygate_data, encryption_key = ''):
        checksum = ""
        payload = ""
        for key, value in paygate_data.items():
            payload += str(value) 
        if encryption_key != '':
            payload += f"{encryption_key}"
            checksum = hashlib.md5(payload.encode('utf-8')).hexdigest()
        return checksum

    def cleanResponseData(self, response_data):
        cleaned_response_data = {}
        for data_piece in response_data:
            split_data = data_piece.split("=")
            cleaned_response_data[split_data[0]] = split_data[1]
        return cleaned_response_data

    def verifyDataIntegrity(self, cleaned_response_data:dict, secret="secret"):
        checksum_to_compare = cleaned_response_data["CHECKSUM"]
        del cleaned_response_data["CHECKSUM"]
        values_as_string = "".join(list(cleaned_response_data.values()))
        values_as_string += secret
        checksum = hashlib.md5(values_as_string.encode('utf-8')).hexdigest()
        if checksum_to_compare == checksum:
            return True
        else:
            return False

    def getMerchantEncryptionKey(paygate_id:int):
        return "secret"

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


