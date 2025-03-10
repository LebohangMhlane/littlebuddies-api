import uuid
import requests
import json
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.merchants.models import Branch, SaleCampaign
from apps.orders.models import Order, OrderedProduct
from apps.products.models import BranchProduct
from apps.transactions.models import Transaction
from .models import Payment


class InitializePaymentView(APIView):

    permission_classes = []

    def post(self, request):
        try:
            # prepare the order data, create the ordered products and transaction:
            transaction = self.prepare_the_order_data(request)

            # once the order data has been prepared and verified successfully, we can now initialize the payment:
            if transaction:
                return self.initialize_paystack_payment(
                    request, transaction=transaction
                )
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "payment_url": "",
                    "message": f"Failed to initialize payment: {e}",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def create_a_transaction(self, request, branch, order_amount, products_ordered):
        try:
            transaction = Transaction()
            # Generate a unique transaction reference
            transaction.reference = str(uuid.uuid4())
            transaction.customer = request.user.useraccount
            transaction.branch = branch
            transaction.total_with_service_fee = order_amount
            transaction.total_minus_service_fee = round(order_amount * 0.82, 2)
            transaction.save()
            transaction.products_ordered.set(products_ordered)
            transaction.save()

            return transaction
        except Exception as e:
            raise Exception(f"Failed to create a transaction: {e}")

    def create_a_order(self, request, transaction: Transaction):
        try:
            # get the merchant this order belongs to:
            merchant_business = transaction.branch.merchant

            # create the order:
            order = Order()
            order.customer = request.user.useraccount
            order.transaction = transaction
            order.status = Order.PAYMENT_PENDING
            order.delivery = request.data["is_delivery"]
            order.delivery_fee = merchant_business.delivery_fee
            order.delivery_date = request.data["delivery_date"]
            order.delivery_address = request.data["delivery_address"]
            order.save()

            return order
        except Exception as e:
            raise Exception(f"Failed to create an order: {e}")

    def prepare_the_order_data(self, request):

        def create_ordered_products():
            products_ordered = []
            previously_processed_order_id = 0
            for id in ordered_product_ids:
                # we dont want to process a product that has already been processed:
                if id == previously_processed_order_id:
                    continue
                else:
                    previously_processed_order_id = id

                try:
                    # get the product:
                    branch_product = BranchProduct.objects.get(id=id, branch=branch)

                    # create the ordered product:
                    ordered_product = OrderedProduct()
                    ordered_product.branch_product = branch_product

                    # find the sale campaign if there was one:
                    sale_campaign = SaleCampaign.objects.filter(
                        branch_product=branch_product, branch=branch
                    )
                    if sale_campaign.count() > 0:  # TODO: test sale campaign:
                        # set the sale_campaign:
                        sale_campaign = sale_campaign.first()
                        ordered_product.sale_campaign = sale_campaign

                        # set the order price / we must take the sale campaign into account:
                        sale_campaign_price = (
                            sale_campaign.calculate_sale_campaign_price()
                        )
                        ordered_product.order_price = sale_campaign_price
                    else:
                        ordered_product.order_price = branch_product.branch_price

                    # set how many items of this product was ordered:
                    ordered_product.quantity_ordered = ordered_product_ids.count(id)

                    # save the ordered product:
                    ordered_product.save()

                    # store it in the list:
                    products_ordered.append(ordered_product)

                except Exception as e:
                    raise Exception(f"Failed to create ordered product: {e}")

            # TODO: code accounting:
            # calculate all the total amounts for each product and it must match exactly the total amount of the order price:
            return products_ordered

        try:
            # get the order data from the request:
            ordered_product_ids = request.data["ordered_products"]
            branch = request.data["branch"]

            # get the order amount from the order data:
            order_amount = float(request.data["amount"])

            # find the branch the order belongs to:
            branch = Branch.objects.get(id=branch)
            # the branch must be active:
            assert branch.is_active, f"{branch.address} - This branch is not active."

            # get the products ordered:
            products_ordered = create_ordered_products()

            # create the transaction:
            transaction = self.create_a_transaction(
                request, branch, order_amount, products_ordered
            )

            # now we create an order:
            self.create_a_order(request, transaction)

            return transaction
        except Exception as e:
            raise e

    def initialize_paystack_payment(self, request, transaction: Transaction = None):

        # prepare the payload we send to paystack to initialize the payment:
        email = request.user.email
        amount = float(request.data.get("amount"))  # Paystack expects amount in cents

        # set the authentication paystack requires:
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }

        # set the payload:
        data = {
            "email": email,
            "amount": amount * 100,  # Convert to kobo (or cents)
            "reference": transaction.reference,
        }

        # send the payload to paystack to initialize the payment process:
        response = requests.post(
            "https://api.paystack.co/transaction/initialize", json=data, headers=headers
        )

        if response.status_code == 200:
            # convert the response to readable json:
            response_data = response.json()

            if response_data.get("status"):
                # create the payment in the database:
                payment = Payment.objects.create(
                    email=email, amount=amount, reference=transaction.reference
                )

                # add the payment to the transaction:
                transaction.payment = payment
                transaction.save()

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

                # update the transaction status:

                # create the order:

                # send order emails:
                pass

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
