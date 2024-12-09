import json
import datetime
import hashlib
import requests

from django.http import HttpResponse
from django.conf import settings
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.integrations.firebase_integration.firebase_module import FirebaseInstance
from apps.merchants.models import Branch
from apps.orders.models import Order
from apps.orders.serializers.order_serializer import OrderSerializer
from apps.paygate.app_models.app_models import CheckoutForm
from apps.transactions.models import Transaction
from apps.transactions.serializers.transaction_serializer import TransactionSerializer

from global_view_functions.global_view_functions import GlobalViewFunctions

from global_test_config.global_test_config import GlobalTestCaseConfig

class PaymentInitializationView(APIView, GlobalViewFunctions, GlobalTestCaseConfig):

    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            checkout_form = CheckoutForm(payload=request.data)
            branch = self.get_branch(checkout_form.branchId)
            if checkout_form.verify_purchase():
                paygate_payload, reference = self.prepare_paygate_payload(checkout_form, branch, request)
                paygate_response = self.send_initiate_payment_request_to_paygate(paygate_payload)
                
                if paygate_response.status_code == 200:
                    response_as_a_dict = self.convert_response_to_dict(paygate_response.text.split("&"))
                    data_integrity_secure, verified_payload = self.verify_payload_integrity(
                        response_as_a_dict, secret=branch.merchant.get_merchant_secret_key()
                    )
                    
                    if data_integrity_secure:
                        transaction = self.create_a_transaction(request, checkout_form, branch, reference, verified_payload)
                        if transaction:
                            order = self.create_an_order(transaction, checkout_form)
                            return self.return_success_response(verified_payload, transaction, order)
                        else:
                            raise Exception("Transaction creation failed")
                    else:
                        raise Exception("Data integrity not secure")
                else:
                    raise Exception(f"Response from Paygate was {paygate_response.status_code}")
        except Exception as e:
            return self.errorResponse(str(e))

    def prepare_paygate_payload(self, checkout_form_payload: CheckoutForm, branch: Branch, request):
        reference = self.create_a_reference(branch, request)
        total_checkout_amount = checkout_form_payload.total_checkout_amount.replace(".", "") # paygate doesn't use decimals
        paygate_payload = {
            "PAYGATE_ID": branch.merchant.paygate_id,
            "REFERENCE": reference,
            "AMOUNT": f"{total_checkout_amount}", 
            "CURRENCY": "ZAR",
            "RETURN_URL": f"{settings.SERVER_URL}/payment_notification/",
            "TRANSACTION_DATE": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "LOCALE": "en-za",
            "COUNTRY": "ZAF",
            "EMAIL": branch.merchant.user_account.user.email,
        }
        paygate_payload["CHECKSUM"] = self.generateChecksum(paygate_payload, branch.merchant.get_merchant_secret_key())
        return paygate_payload, reference

    def create_a_reference(self, branch: Branch, request):
        number_of_branch_transactions = Transaction.objects.filter(branch=branch).count()
        reference = f"T{branch.id}{str(request.user.useraccount.phone_number)[-4:]}{request.user.pk}{number_of_branch_transactions}"
        return reference

    def generateChecksum(self, paygate_data, merchantPaygateSecretKey=""):
        payload = "".join(str(value) for value in paygate_data.values())
        if merchantPaygateSecretKey:
            payload += merchantPaygateSecretKey
        return hashlib.md5(payload.encode("utf-8")).hexdigest()

    def convert_response_to_dict(self, response_data):
        return dict(data_piece.split("=") for data_piece in response_data)

    def send_initiate_payment_request_to_paygate(self, paygatePayload):
        return requests.post(settings.PAYGATE_INITIATE_PAYMENT_URL, data=paygatePayload)

    def create_a_transaction(self, request, checkout_form_payload: CheckoutForm, branch: Branch, reference, verifiedPayload):
        if not Transaction.objects.filter(
            payRequestId=verifiedPayload["PAY_REQUEST_ID"],
            reference=reference,
            customer=request.user.useraccount,
            branch=branch,
            amount=checkout_form_payload.total_checkout_amount,
            productsPurchased__id__in=checkout_form_payload.productIds,
            numberOfProducts=checkout_form_payload.productCount,
            discountTotal=checkout_form_payload.discountTotal,
            status=Transaction.PENDING,
        ).exists():
            transaction = Transaction.objects.create(
                payRequestId=verifiedPayload["PAY_REQUEST_ID"],
                reference=reference,
                customer=request.user.useraccount,
                branch=branch,
                amount=checkout_form_payload.total_checkout_amount,
                numberOfProducts=checkout_form_payload.productCount,
                status=Transaction.PENDING,
                discountTotal=checkout_form_payload.discountTotal,
                dateCreated=datetime.datetime.now(),
            )
            transaction.productsPurchased.set(checkout_form_payload.branch_products)
            transaction.save()
            return transaction
        return Transaction.objects.filter(
            payRequestId=verifiedPayload["PAY_REQUEST_ID"],
            reference=reference,
            customer=request.user.useraccount,
            branch=branch,
            amount=str(checkout_form_payload.total_checkout_amount),
            productsPurchased__id__in=checkout_form_payload.branch_products,
            numberOfProducts=checkout_form_payload.productCount,
            discountTotal=checkout_form_payload.discountTotal,
            status=Transaction.PENDING,
        ).first()

    def create_an_order(self, transaction: Transaction, checkoutForm: CheckoutForm):
        try:
            order = Order.objects.create(
                transaction=transaction,
                status=Order.PAYMENT_PENDING,
                delivery=checkoutForm.delivery,
                deliveryDate=checkoutForm.deliveryDate,
                address=checkoutForm.address,
            )
            order.orderedProducts.add(*transaction.productsPurchased.all())
            order.save()
            for orderedProduct in transaction.productsPurchased.all():
                orderedProduct.order = order
                orderedProduct.save()
            return order
        except Exception as e:
            raise Exception(f"Failed to create order: {e.args[0]}")

    def return_success_response(self, verifiedPayload, transaction, order):
        orderSerializer = OrderSerializer(order, many=False)
        transactionSerializer = TransactionSerializer(transaction, many=False)
        return Response(
            {
                "success": True,
                "message": "Paygate response was successful",
                "paygatePayload": verifiedPayload,
                "transaction": transactionSerializer.data,
                "order": orderSerializer.data,
            },
            content_type="application/json",
            status=200,
        )

    def errorResponse(self, error_message):
        return Response(
            {
                "success": False,
                "message": "Failed to initialize Paygate payment",
                "error": error_message,
            },
            content_type="application/json",
            status=500,
        )


class PaymentNotificationView(APIView, GlobalViewFunctions):

    permission_classes = []

    def post(self, request, *args, **kwargs):
        try:
            updatedTransaction = self.verifyAndUpdateTransactionStatus(request.data)
            self.update_and_send_notification(updatedTransaction)
        except Exception as e:
            pass
        return HttpResponse("OK")

    def verifyAndUpdateTransactionStatus(self, receivedPayload):
        def setTransactionStatus(transactionStatus, transaction: Transaction):
            if transactionStatus == 0:
                transaction.status = Transaction.NOT_DONE
            elif transactionStatus == 1:
                transaction.status = Transaction.COMPLETED
            elif transactionStatus == 2:
                transaction.status = Transaction.DECLINED
            elif transactionStatus == 3:
                transaction.status = Transaction.CANCELLED
            elif transactionStatus == 4:
                transaction.status = Transaction.CUSTOMER_CANCELLED
            elif transactionStatus == 5:
                transaction.status = Transaction.RECEIVED_BY_PAYGATE
            elif transactionStatus == 7:
                transaction.status = Transaction.SETTLEMENT_VOIDED
            return transaction

        try:
            payRequestId = receivedPayload["PAY_REQUEST_ID"]
            transaction = Transaction.objects.filter(payRequestId=payRequestId).first()
            dataIntegritySecure, validatedPayload = self.verify_payload_integrity(
                receivedPayload,
                secret=transaction.branch.merchant.get_merchant_secret_key(),
            )  # TODO: investigate checksum check failure in this step:
            transactionStatus = int(validatedPayload["TRANSACTION_STATUS"])
            transaction = setTransactionStatus(transactionStatus, transaction)
            transaction.save()
            return transaction
        except Exception as e:
            # we cannot return an error response to paygate in this view
            pass

    def updateOrder(self, transaction):
        order = Order.objects.get(transaction=transaction)
        if order:
            if order.transaction.status == Transaction.COMPLETED:
                order.status = order.PENDING_DELIVERY
            else:
                order.status = order.transaction.status
            order.save()
            return order
        return None
    
    def update_and_send_notification(self, updatedTransaction):
        order = self.updateOrder(updatedTransaction)
        _ = FirebaseInstance().send_transaction_status_notification(
            updatedTransaction
        )
        self.sendOrderEmail(updatedTransaction, order)

    def sendOrderEmail(self, updatedTransaction, order):
        pass


class PaymentSuccessView(APIView):

    permission_classes = []

    def get(self, request, *args, **kwargs):
        return render(
            request=request,
            template_name="payfast_templates/payment_successful_page.html",
            context={},
        )


class PaymentCancelledView(APIView):

    http_method_names = ["GET"]

    def get(self, request, *args):
        return Response(
            {
                "cancellation_received": True,
            }
        )
