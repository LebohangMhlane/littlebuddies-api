
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import datetime
from django.db import transaction
import logging

from apps.orders.models import Order, record_cancellation
from apps.orders.serializers.order_serializer import OrderSerializer
from apps.transactions.models import Transaction
from apps.merchants.models import SaleCampaign
from global_view_functions.global_view_functions import GlobalViewFunctions

logger = logging.getLogger(__name__)

class GetAllOrdersView(APIView, GlobalViewFunctions):

    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, **kwargs):
        try:
            if self.if_user_is_merchant(request):
                orders = self.get_orders_as_merchant(request)
            else:
                orders = self.get_orders_as_customer(request)
            orders = OrderSerializer(orders, many=True)
            orders = orders.data
            orders = self.modify_orders_that_had_specials(orders)
            return Response({
                "success": True,
                "message": "Orders retrieved successfully",
                "orders": orders
            })
        except Exception as e:
            return Response({
                "success": False,
                "message": "Failed to get Orders",
                "error": str(e)
            })

    def get_orders_as_merchant(self, request):
        user_account = request.user.useraccount
        orders = Order.objects.filter(
            transaction__branch__merchant__user_account__pk=user_account.pk, 
            transaction__status=Transaction.COMPLETED
        )
        if orders:
            return orders

    def get_orders_as_customer(self, request):
        user_account = request.user.useraccount
        orders = Order.objects.filter(
            status__in=[Order.PENDING_DELIVERY, Order.DELIVERED],
            transaction__customer__id=user_account.pk, 
            transaction__status=Transaction.COMPLETED).order_by("created")
        if orders:
            return orders

    def modify_orders_that_had_specials(self, orders):
        for order in orders:
            for ordered_product in order["ordered_products"]:
                if ordered_product["sale_campaign"]:
                    self._adjust_prices_based_on_sale_campaigns(
                        ordered_product["sale_campaign"], ordered_product)
        return orders

    def _adjust_prices_based_on_sale_campaigns(self, sale_campaign, ordered_product):
        discount = sale_campaign["percentage_off"]
        discounted_price = float(ordered_product["branch_product"]["branch_price"]) * (1 - discount / 100)
        ordered_product["branch_product"]["branch_price"] = str(f"{discounted_price:.2f}")

class CancelOrder(APIView, GlobalViewFunctions):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        order_id = kwargs.get("order_id")
        if not order_id:
            return Response(
                {"success": False, "message": "Order ID is required!"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order = get_object_or_404(Order, id=order_id)
        
        if order.transaction.customer.user != request.user:
            return Response(
                {"success": False, "message": "You are not authorized to cancel this order."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if order.status in [Order.CANCELLED, Order.DELIVERED]:
            return Response(
                {"success": False, "message": "Order cannot be cancelled at this stage."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            order.status = Order.CANCELLED
            order.acknowledged = False
            order.save()
            
            # we can improve by creating an excel file as well
            record_cancellation(
                order=order,
                user_account=request.user.useraccount,
                reason='CUSTOMER_REQUEST',
                notes=request.data.get('cancellation_notes', ''),
                refund_amount=order.total_amount if request.data.get('initiate_refund') else None
            )

            try:
                # Notify customer
                customer_context = {'order': order}
                customer_html_message = render_to_string('email_templates/order_cancelled_customer.html', customer_context)
                customer_plain_message = strip_tags(customer_html_message)

                send_mail(
                    subject='Your Order Has Been Cancelled',
                    message=customer_plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[order.transaction.customer.user.email],
                    html_message=customer_html_message,
                )

                # Notify merchant
                merchant_context = {'order': order}
                merchant_html_message = render_to_string('email_templates/order_cancelled_merchant.html', merchant_context)
                merchant_plain_message = strip_tags(merchant_html_message)

                send_mail(
                    subject='Order Cancelled',
                    message=merchant_plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[order.transaction.branch.merchant.user_account.user.email], 
                    html_message=merchant_html_message,
                )
            except Exception as e:
                return Response(
                    {"success": False, "message": f"Order cancelled, but emails failed to send: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return Response(
            {
                "success": True,
                "message": "Order cancelled successfully!",
            },
            status=status.HTTP_200_OK,
        )
    
class RepeatOrder(APIView, GlobalViewFunctions):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, order_id):
        try:
            order = Order.objects.prefetch_related(
                "ordered_products__branch_product__product"
            ).get(id=order_id)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        branch = order.transaction.branch

        product_list = []
        out_of_stock = []
        price_changes = []
        new_cost = 0.00

        active_sales = SaleCampaign.objects.filter(
            branch=branch,
            campaign_ends__gte=datetime.datetime.now()
        )

        for ordered_product in order.ordered_products.all():
            branch_product = ordered_product.branch_product
            special_price = branch_product.branch_price

            if branch_product.in_stock:
                sale_campaign = active_sales.filter(branch_product=branch_product).first()
                if sale_campaign:
                    discount = sale_campaign.percentage_off
                    special_price = float(branch_product.branch_price) * (1 - discount / 100)

                product_details = {
                    "product_id": branch_product.product.id,
                    "name": branch_product.product.name,
                    "quantity_ordered": ordered_product.quantity_ordered,
                    "current_price": special_price,
                }

                if branch_product.branch_price != special_price:
                    price_changes.append({
                        "product_id": branch_product.product.id,
                        "name": branch_product.product.name,
                        "old_price": branch_product.branch_price,
                        "new_price": special_price,
                    })

                new_cost += float(special_price) * ordered_product.quantity_ordered
                product_list.append(product_details)
            else:
                out_of_stock.append({
                    "product_id": branch_product.product.id,
                    "name": branch_product.product.name,
                })

        response_data = {
            "success": True,
            "order_id": order.id,
            "branch": {
                "id": branch.id,
                "name": branch.address,
            },
            "product_list": product_list,
            "new_cost": f"R {new_cost:.2f}",
            "out_of_stock": out_of_stock,
            "price_changes": price_changes,
        }

        try:
            customer_email = order.transaction.customer.user.email
            if not customer_email:
                return Response(
                    {"error": "No customer email available"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            customer_context = {
                'order': order,
                'product_list': product_list,
                'out_of_stock': out_of_stock,
                'price_changes': price_changes,
                'new_cost': new_cost,
            }
            customer_html_message = render_to_string('email_templates/repeat_order_summary.html', customer_context)
            customer_plain_message = strip_tags(customer_html_message)

            send_mail(
                subject='Repeat Order Summary',
                message=customer_plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[customer_email],
                html_message=customer_html_message,
            )
        except Exception as e:
            logger.error(f"Email sending failed: {str(e)}")
            return Response(
                {"error": "Failed to send email", "details": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(response_data, status=status.HTTP_200_OK)