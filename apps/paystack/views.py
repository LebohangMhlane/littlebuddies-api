import uuid
import requests
import json
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Payment


class InitializePaymentView(APIView):

    permission_classes = []

    def post(self, request):
        try:
            # prepare the payload we send to paystack to initialize the payment:
            email = request.data.get("email")
            amount = float(request.data.get("amount"))  # Paystack expects amount in cents
            reference = str(uuid.uuid4())  # Generate a unique transaction reference

            # set the authentication paystack requires:
            headers = {
                "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
                "Content-Type": "application/json",
            }

            # set the payload:
            data = {
                "email": email,
                "amount": amount * 100,  # Convert to kobo (or cents)
                "reference": reference,
            }

            # send the payload to paystack to initialize the payment process:
            response = requests.post(
                "https://api.paystack.co/transaction/initialize", json=data, headers=headers
            )

            if response.status_code == 200:
                # convert the response to readable json:
                response_data = response.json()

                # create the payment in the database:
                if response_data.get("status"):
                    Payment.objects.create(email=email, amount=amount, reference=reference)
                    return Response(
                        {
                            "success": True,
                            "payment_url": response_data["data"]["authorization_url"],
                            "message": "Payment initialized successfully!",
                        },
                        status=status.HTTP_201_CREATED,
                    )
            else:
                raise Exception("Failed to initialize payment")
        except Exception as e:
            # return an error response:
            return Response(
                {
                    "success": False,
                    "payment_url": "",
                    "message": f"Failed to initialize payment: {e}",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class VerifyPaymentView(APIView):
    def get(self, request, reference):
        url = f"https://api.paystack.co/transaction/verify/{reference}"
        headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}

        response = requests.get(url, headers=headers)
        response_data = response.json()

        if response_data.get("status") and response_data["data"]["status"] == "success":
            # Update payment record
            payment = Payment.objects.filter(reference=reference).first()
            if payment:
                payment.paid = True
                payment.save()
            return Response(
                {"message": "Payment verified successfully"}, status=status.HTTP_200_OK
            )

        return Response(
            {"error": "Payment verification failed"}, status=status.HTTP_400_BAD_REQUEST
        )


class PaystackWebhookView(APIView):
    def post(self, request):
        payload = json.loads(request.body)

        if payload.get("event") == "charge.success":
            reference = payload["data"]["reference"]
            payment = Payment.objects.filter(reference=reference).first()
            if payment:
                payment.paid = True
                payment.save()
            return Response(
                {"message": "Payment updated successfully"}, status=status.HTTP_200_OK
            )

        return Response({"error": "Invalid event"}, status=status.HTTP_400_BAD_REQUEST)
