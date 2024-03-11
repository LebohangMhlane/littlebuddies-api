import json
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import hashlib
import urllib.parse
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
        payfast_data = self.getPayFastData(request=request)
        try:
            payfast_sandbox_url = "https://sandbox.payfast.co.za/eng/process"
            response = requests.post(
                payfast_sandbox_url,
                data=payfast_data
            )
            return Response({"success": True, "payFastUrl": response.url}, content_type='application/json')
        except:
            print("An error has occurred")
            return Response({"success": False, "payFastUrl": ""}, content_type='application/json')
    
    def getPayFastData(self, request):
        payfast_data = {
            "merchant_id": "10000100",
            "merchant_key": "46f0cd694581a",
            "return_url": f"{settings.SERVER_URL}/payment_successful/",
            "notify_url": f"{settings.SERVER_URL}/payment_notification/",
            "m_payment_id": "UniqueId",
            "amount": "200",
            "item_name": "test product",
            "payment_method": "cc",
        }
        passphrase = 'jt7NOE43FZPn'
        payfast_data["signature"] = self.generateSignature(payfast_data=payfast_data, passPhrase=passphrase)
        return payfast_data

    def generateSignature(self, payfast_data, passPhrase = ''):
        payload = ""
        for key in payfast_data:
            payload += key + "=" + urllib.parse.quote_plus(payfast_data[key].replace("+", " ")) + "&"
        payload = payload[:-1]
        if passPhrase != '':
            payload += f"&passphrase={passPhrase}"
        return hashlib.md5(payload.encode()).hexdigest()


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


