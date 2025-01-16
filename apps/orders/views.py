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

from apps.merchants.serializers.merchant_serializer import BranchSerializer
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
            return Response(
                {
                    "success": True,
                    "message": "Orders retrieved successfully",
                    "orders": orders,
                }
            )
        except Exception as e:
            return Response(
                {"success": False, "message": "Failed to get Orders", "error": str(e)}
            )

    def get_orders_as_merchant(self, request):
        user_account = request.user.useraccount
        orders = Order.objects.filter(
            transaction__branch__merchant__user_account__pk=user_account.pk,
        )
        if orders:
            return orders

    def get_orders_as_customer(self, request):
        user_account = request.user.useraccount
        orders = Order.objects.filter(
            status__in=[Order.PENDING_DELIVERY, Order.DELIVERED],
            transaction__customer__id=user_account.pk,
            transaction__status=Transaction.COMPLETED,
        ).order_by("created")
        if orders:
            return orders

    def modify_orders_that_had_specials(self, orders):
        for order in orders:
            for ordered_product in order["ordered_products"]:
                if ordered_product["sale_campaign"]:
                    self._adjust_prices_based_on_sale_campaigns(
                        ordered_product["sale_campaign"], ordered_product
                    )
        return orders

    def _adjust_prices_based_on_sale_campaigns(self, sale_campaign, ordered_product):
        discount = sale_campaign["percentage_off"]
        discounted_price = float(ordered_product["branch_product"]["branch_price"]) * (
            1 - discount / 100
        )
        ordered_product["branch_product"]["branch_price"] = str(
            f"{discounted_price:.2f}"
        )


class CancelOrder(APIView, GlobalViewFunctions):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        order_id = kwargs.get("order_id")
        if not order_id:
            return Response(
                {"success": False, "message": "Order ID is required!"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order = get_object_or_404(Order, id=order_id)

        if order.transaction.customer.user != request.user:
            return Response(
                {
                    "success": False,
                    "message": "You are not authorized to cancel this order.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if order.status in [Order.CANCELLED, Order.DELIVERED]:
            return Response(
                {
                    "success": False,
                    "message": "Order cannot be cancelled at this stage.",
                },
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
                reason="CUSTOMER_REQUEST",
                notes=request.data.get("cancellation_notes", ""),
                refund_amount=(
                    order.total_amount if request.data.get("initiate_refund") else None
                ),
            )

            try:
                # Notify customer
                customer_context = {"order": order}
                customer_html_message = render_to_string(
                    "email_templates/order_cancelled_customer.html", customer_context
                )
                customer_plain_message = strip_tags(customer_html_message)

                send_mail(
                    subject="Your Order Has Been Cancelled",
                    message=customer_plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[order.transaction.customer.user.email],
                    html_message=customer_html_message,
                )

                # Notify merchant
                merchant_context = {"order": order}
                merchant_html_message = render_to_string(
                    "email_templates/order_cancelled_merchant.html", merchant_context
                )
                merchant_plain_message = strip_tags(merchant_html_message)

                send_mail(
                    subject="Order Cancelled",
                    message=merchant_plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[
                        order.transaction.branch.merchant.user_account.user.email
                    ],
                    html_message=merchant_html_message,
                )
            except Exception as e:
                return Response(
                    {
                        "success": False,
                        "message": f"Order cancelled, but emails failed to send: {str(e)}",
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return Response(
            {
                "success": True,
                "message": "Order cancelled successfully!",
            },
            status=status.HTTP_200_OK,
        )


class checkForOrderChangesView(APIView, GlobalViewFunctions):

    '''
    This endpoint only checks for changes within the orders products such as
    price changes and availability in terms of stock or if they are still active (still being sold)
    '''

    permission_classes = []

    order = None

    ordered_products = None

    order_changes = {
        "branch": None,
        "order_id": 0,
        "price_changes": {},
        "out_of_stock": {},
        "no_longer_sold": {},
        "new_total": {},
    }

    def return_successful_response(self):
        return Response(
            {
                "success": True,
                "message": "Order changes checked successfully!",
                "order_changes": self.order_changes,
            }
        )

    def return_failed_response(self, error_message=""):
        return Response(
            {
                "success": False,
                "message": f"Failed to check Order: {error_message}",
                "order_changes": {},
            }, status=500
        )

    def get_order(self, order_id):
        order = Order.objects.prefetch_related(
            "ordered_products__branch_product__product"
        ).get(id=order_id)
        return order

    def check_for_price_changes(self):
        branch = self.order.transaction.branch
        sale_campaigns = SaleCampaign.objects.filter(branch=branch, active=True)

        # we need to check if the branch updated their prices recently:
        branch_products = branch.branchproduct_set.filter(in_stock=True, is_active=True)
        for product in self.ordered_products.filter(branch_product__is_active=True):
            for branch_product in branch_products:
                if product.branch_product == branch_product:
                    price_on_order = product.order_price
                    self.order_changes["price_changes"][product.id] = {
                        "previous_order_price": price_on_order,
                        "new_order_price": branch_product.branch_price,
                    }
                    break

        # now we check for price changes based on if the product is on sale:
        if sale_campaigns:
            for product in self.ordered_products.filter(branch_product__is_active=True):
                for sale_campaign in sale_campaigns:
                    if sale_campaign.branch_product == product.branch_product:
                        price_on_order = product.order_price
                        sale_campaign_price = (
                            sale_campaign.calculate_sale_campaign_price()
                        )
                        if price_on_order != sale_campaign_price:
                            product_id = product.id
                            if product_id not in self.order_changes["price_changes"]:
                                self.order_changes["price_changes"][product_id] = {}
                            self.order_changes["price_changes"][product_id][
                                "sale_campaign_price"
                            ] = sale_campaign_price
                        break

    def check_for_items_out_of_stock(self):
        for ordered_product in self.ordered_products:
            if not ordered_product.branch_product.in_stock:
                self.order_changes["out_of_stock"][ordered_product.id] = {
                    "name": ordered_product.branch_product.product.name,
                }
            if not ordered_product.branch_product.is_active:
                self.order_changes["no_longer_sold"][ordered_product.id] = {
                    "name": ordered_product.branch_product.product.name,
                }

    def calculate_the_new_total_price(self):
        new_order_total = 0.00
        for order_id, price_changes in self.order_changes["price_changes"].items():
            new_order_total += (
                float(price_changes["new_order_price"])
                if not "sale_campaign_price" in price_changes
                else float(price_changes["sale_campaign_price"])
            )
        self.order_changes["old_total"] = float(self.order.transaction.amount)
        self.order_changes["new_total"] = new_order_total

    def get(self, request, *args, **kwargs):
        try:
            self.order_changes['order_id'] = kwargs.get("order_id")
            self.order = self.get_order(order_id=kwargs.get("order_id"))
            self.order_changes["branch"] = BranchSerializer(
                self.order.transaction.branch, many=False
            ).data
            self.ordered_products = self.order.ordered_products.all()
            self.check_for_items_out_of_stock()
            self.check_for_price_changes()
            self.calculate_the_new_total_price()
            return self.return_successful_response()
        except Exception as e:
            return self.return_failed_response(error_message=e.args[0])


class RepeatOrder(APIView, GlobalViewFunctions):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, order_id):
        try:
            order = Order.objects.prefetch_related(
                "ordered_products__branch_product__product"
            ).get(id=order_id)
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND
            )

        branch = order.transaction.branch

        product_list = []
        out_of_stock = []
        price_changes = []
        new_cost = 0.00

        active_sales = SaleCampaign.objects.filter(
            branch=branch, campaign_ends__gte=datetime.datetime.now()
        )

        for ordered_product in order.ordered_products.all():
            branch_product = ordered_product.branch_product
            special_price = branch_product.branch_price

            if branch_product.in_stock:
                sale_campaign = active_sales.filter(
                    branch_product=branch_product
                ).first()
                if sale_campaign:
                    discount = sale_campaign.percentage_off
                    special_price = float(branch_product.branch_price) * (
                        1 - discount / 100
                    )

                product_details = {
                    "product_id": branch_product.product.id,
                    "name": branch_product.product.name,
                    "quantity_ordered": ordered_product.quantity_ordered,
                    "current_price": special_price,
                }

                if branch_product.branch_price != special_price:
                    price_changes.append(
                        {
                            "product_id": branch_product.product.id,
                            "name": branch_product.product.name,
                            "old_price": branch_product.branch_price,
                            "new_price": special_price,
                        }
                    )

                new_cost += float(special_price) * ordered_product.quantity_ordered
                product_list.append(product_details)
            else:
                out_of_stock.append(
                    {
                        "product_id": branch_product.product.id,
                        "name": branch_product.product.name,
                    }
                )

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
                    status=status.HTTP_400_BAD_REQUEST,
                )

            customer_context = {
                "order": order,
                "product_list": product_list,
                "out_of_stock": out_of_stock,
                "price_changes": price_changes,
                "new_cost": new_cost,
            }
            customer_html_message = render_to_string(
                "email_templates/repeat_order_summary.html", customer_context
            )
            customer_plain_message = strip_tags(customer_html_message)

            send_mail(
                subject="Repeat Order Summary",
                message=customer_plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[customer_email],
                html_message=customer_html_message,
            )
        except Exception as e:
            logger.error(f"Email sending failed: {str(e)}")
            return Response(
                {"error": "Failed to send email", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(response_data, status=status.HTTP_200_OK)
