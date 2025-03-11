import uuid
import requests
import json
from django.conf import settings
from django.db import transaction
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
            transaction = self.process_the_order(request)

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

    def create_ordered_products(self, ordered_product_ids, branch, order_amount):
        with transaction.atomic():
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

                    # find the sale campaign if there is one:
                    sale_campaign = SaleCampaign.objects.filter(
                        branch_product=branch_product, branch=branch
                    )
                    if sale_campaign.count() > 0:
                        # set the sale_campaign:
                        sale_campaign = sale_campaign[0]
                        ordered_product.sale_campaign = sale_campaign

                        # set the order price / we must take the sale campaign into account:
                        sale_campaign_price = (
                            sale_campaign.calculate_sale_campaign_price()
                        )
                        # the final price they are buying the product for after sale campaign discount is applied:
                        ordered_product.order_price = sale_campaign_price 
                    else:
                        # the original price of the product:
                        ordered_product.order_price = branch_product.branch_price

                    # set how many items of this product was ordered:
                    ordered_product.quantity_ordered = ordered_product_ids.count(id)

                    # save the ordered product:
                    ordered_product.save()

                    # store it in the list:
                    products_ordered.append(ordered_product)

                except Exception as e:
                    raise Exception(f"Failed to create ordered product: {e}")

            # balance the amount:
            # fail this if the amount calculated does not match the order amount:
            self.balance_the_total_amount(products_ordered, order_amount)

        return products_ordered

    def balance_the_total_amount(self, products_ordered, order_amount):
        '''
        We need to ensure that the calculations done here match the calculations
        done on the mobile app. Stop the payment process if this fails
        '''
        try:
            # get the total amount for the whole order minus the delivery fee:
            total_amount_minus_delivery_fee = 0.00
            for product in products_ordered:
                # if the product has more than one of itself ordered then calculate the total amount:
                if product.quantity_ordered > 1:
                    total_amount_of_all = float(product.order_price * product.quantity_ordered)
                    total_amount_minus_delivery_fee += total_amount_of_all
                else:
                    total_amount_minus_delivery_fee += float(product.order_price)
            # get the delivery fee:
            delivery_fee = float(product.branch_product.branch.merchant.delivery_fee)
            # add the delivery fee to the total amount:
            total_amount_minus_delivery_fee += delivery_fee
            # verify that the amounts match:
            balancing_error_text = "Balancing failed: Total amount calculated does not match the order amount"
            assert total_amount_minus_delivery_fee == order_amount, balancing_error_text
        except Exception as e:
            raise e

    def process_the_order(self, request):
        try:
            # find the branch this order belongs to:
            # the branch must be active:
            branch = Branch.objects.get(id=request.data["branch"])
            assert branch.is_active, f"{branch.address} - This branch is not active."

            # get the order amount for accounting:
            order_amount = float(request.data["amount"])

            # create the ordered products:
            ordered_product_ids = request.data["ordered_products"]
            products_ordered = self.create_ordered_products(
                ordered_product_ids, branch, order_amount
            )

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
            raise Exception(
                f"Failed to initialize payment: Response from Paystack was not 200. It was returned: {response.status_code}"
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

    permission_classes = []

    def post(self, request):

        # the post request data from paystack:
        payload = json.loads(request.body)

        # if the payment was successful:
        if payload.get("event") == "charge.success":
            # get the payment:
            reference = payload["data"]["reference"]
            payment = Payment.objects.filter(reference=reference).first()

            if payment:
                # update the payment status:
                payment.paid = True
                payment.save()

                # update the transaction status:
                transaction = Transaction.objects.filter(reference=reference).first()
                transaction.status = "COMPLETED"
                transaction.save()

                # update the order status:
                order = Order.objects.filter(transaction=transaction).first()
                if order.delivery:
                    order.status = "PENDING_DELIVERY"
                else:
                    order.status = "PENDING_PICKUP"

            return Response(
                {"message": "Payment updated successfully"}, status=status.HTTP_200_OK
            )

        return Response({"error": "Invalid event"}, status=status.HTTP_400_BAD_REQUEST)
