import uuid
import requests
import json
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.merchants.models import Branch, SaleCampaign
from apps.orders.models import OrderedProduct
from apps.products.models import BranchProduct
from apps.transactions.models import Transaction
from .models import Payment


class InitializePaymentView(APIView):

    permission_classes = []

    def post(self, request):
        try:
            # prepare the order data, Order, Transaction, verifying it etc:
            order_data_prepared = self.prepare_the_order_data(request)

            # once the order data has been prepared and verified successfully, we can now initialize the payment:
            if order_data_prepared:
                return self.initialize_paystack_payment(request, transaction=None)
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "payment_url": "",
                    "message": f"Failed to initialize payment: {e}",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def create_a_transaction(self, reference, branch, order_amount, products_ordered):
        try:
            transaction = Transaction()
            transaction.reference = reference
            transaction.branch = branch
            transaction.total_minus_service_fee = round(order_amount * 0.82, 2)
            transaction.products_ordered = products_ordered
        except Exception as e:
            raise Exception(f"Failed to create a transaction: {e}")

    def create_a_order(self):
        pass

    def prepare_the_order_data(self, request):

        def create_ordered_products():
            products_ordered = []
            for id in ordered_product_ids:
                try:
                    # get the product:
                    branch_product = BranchProduct.objects.get(id=id, branch=branch)

                    # create the ordered product:
                    ordered_product = OrderedProduct()
                    ordered_product.branch_product = branch_product

                    # set the sale campaign if there was one:
                    sale_campaign = SaleCampaign.objects.filter(
                        branch_product=branch_product, branch=branch
                    )
                    if sale_campaign.count() > 0:
                        ordered_product.sale_campaign = sale_campaign.first()

                    # set how many items of this product was ordered:
                    ordered_product.quantity_ordered = 2

                    # set the order price:
                    ordered_product.order_price = branch_product.branch_price

                    # save the ordered product:
                    ordered_product.save()

                    # store it in the list:
                    products_ordered.append(ordered_product)
                except Exception as e:
                    raise Exception(f"Failed to create ordered product: {e}")

        try:
            # get the order data from the request:
            ordered_product_ids = request.data["ordered_products"]
            branch = request.data["branch"]
            reference = request.data["reference"]

            # get the order amount from the order data:
            order_amount = float(request.data["amount"])

            # find the branch the order belongs to:
            branch = Branch.objects.get(id=branch)
            # the branch must be active:
            assert branch.is_active, f"{branch.address} - This branch is not active."

            # get the products ordered:
            products_ordered = create_ordered_products()

            # create the transaction:
            transaction = self.create_a_transaction(reference, branch, order_amount)

            return True
        except Exception as e:
            raise e

    def initialize_paystack_payment(self, request, transaction=None):

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
