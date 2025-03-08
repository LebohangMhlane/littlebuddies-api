import uuid
import requests
import json
from django.conf import settings
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Payment


class InitializePaymentView(APIView):
    def post(self, request):
        email = request.data.get("email")
        amount = int(request.data.get("amount"))  # Paystack expects amount in cents
        reference = str(uuid.uuid4())  # Generate a unique transaction reference

        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }
        data = {
            "email": email,
            "amount": amount * 100,  # Convert to kobo (or cents)
            "reference": reference,
        }

        response = requests.post(
            "https://api.paystack.co/transaction/initialize", json=data, headers=headers
        )
        response_data = response.json()

        if response_data.get("status"):
            # Save payment in DB
            Payment.objects.create(email=email, amount=amount, reference=reference)
            return Response(
                {"payment_url": response_data["data"]["authorization_url"]},
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"error": "Failed to initialize payment"},
            status=status.HTTP_400_BAD_REQUEST,
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
