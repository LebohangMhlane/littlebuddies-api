import datetime
from django.conf import settings
from rest_framework.permissions import IsAuthenticated
import json

import googlemaps.addressvalidation
import googlemaps.client
import googlemaps.convert
import googlemaps.directions
import googlemaps.distance_matrix
import googlemaps.geocoding
import googlemaps.geolocation
import googlemaps.maps
import googlemaps.places
from rest_framework.views import APIView
from rest_framework.response import Response

import googlemaps

from apps.integrations.firebase_integration.firebase_module import FirebaseInstance
from apps.merchants.models import Branch, MerchantBusiness, SaleCampaign
from apps.merchants.serializers.merchant_serializer import BranchSerializer, MerchantSerializer, SaleCampaignSerializer

from apps.orders.models import Order, OrderedProduct
from apps.accounts.models import UserAccount
from apps.orders.serializers.order_serializer import OrderSerializer
from apps.products.models import BranchProduct
from apps.products.serializers.serializers import branch_productserializer, ProductSerializer
from global_view_functions.global_view_functions import GlobalViewFunctions
import logging

logger = logging.getLogger(__name__)

class GetStoreRange(APIView, GlobalViewFunctions):
    
    def get(self, request, **kwargs):
        try:
            coordinates = kwargs.get('coordinates') # TODO: find out whats going on here
            mb = MerchantBusiness.objects.all()
            sc = SaleCampaign.objects.filter(branch__merchant__in=mb, campaign_ends__gte=datetime.datetime.now())
            sale_campaigns = []
            if sc: 
                scs = SaleCampaignSerializer(sc, many=True)
                sale_campaigns = scs.data
            if mb: ms = MerchantSerializer(mb, many=True)
            else: raise Exception("No Pet stores were found")
            return Response({
                "success": True,
                "message": "Store range retrieved successfully",
                "petstores": ms.data,
                "sale_campaigns": sale_campaigns
            }, status=200)
        except Exception as e:
            return Response({
                "success": False,
                "message": "Failed to get stores near customer",
                "error": str(e)
            }, status=200)


class GetNearestBranch(APIView, GlobalViewFunctions):
    permission_classes = [IsAuthenticated]
    def get(self, request, **kwargs):
        try:
            # get the coordinates sent by the mobile user:
            coordinates = kwargs["coordinates"]

            # get the merchant business they want to get the nearest branch of:
            merchant_business = MerchantBusiness.objects.get(id=kwargs["merchantId"])

            # initialize the google maps service:
            gmaps_client = googlemaps.Client(key=settings.GOOGLE_SERVICES_API_KEY)

            # get the customers address based on the coordinates:
            customer_address = self._get_customer_address(coordinates, gmaps_client)

            # find the nearest branch of the merchant business that is closes to the customers address:
            branch_data = self._locate_nearest_branch(
                coordinates, 
                merchant_business,
                gmaps_client, 
            )

            # get the last order made from this branch by this user:
            if branch_data:
                branch_id = branch_data["branch"]["id"]
                user = request.user
                last_order = self._get_last_order(user, branch_id)

                # check for and set price changes:
                price_changes = (
                    self._get_price_changes(last_order, branch_data["products"])
                    if last_order else None
                )

            return Response({
                "success": True,
                "message": "Nearest branch retrieved successfully!",
                "nearestBranch": branch_data,
                "customerAddress": customer_address,
                "lastOrder": last_order,
                "priceChanges": price_changes
            }, status=200)

        except Exception as e:
            return Response({
                "success": False,
                "message": "Failed to get nearest branch",
                "error": str(e)
            }, status=400)  

    def _get_last_order(self, user, branch_id):
        try:
            # get the users acccount:
            user_account = UserAccount.objects.get(user=user)

            # get the last order made by the user from this branch:
            last_order = (
                Order.objects.filter(
                    transaction__customer=user_account,
                    transaction__branch_id=branch_id,
                    status="DELIVERED",
                )
                .order_by("-created")
                .first()
            )

            if last_order is not None:
                
                # get the ordered products from the transaction and order:
                order_products = list(last_order.ordered_products.select_related(
                    'branch_product__product'
                ).all())
                transaction_products = list(last_order.transaction.products_ordered.select_related(
                    'branch_product__product'
                ).all())

                # get the products to use from eithe the transaction or the order:
                products_to_use = order_products if order_products else transaction_products
                # prepare the last order data:
                response = {
                    "id": last_order.id,
                    "date": datetime.datetime.strftime(last_order.created, "%Y-%m-%d %H:%M:%S"),
                    "items": [
                        {
                            "product_id": ordered_product.branch_product.id,
                            "name": ordered_product.branch_product.product.name,
                            "quantity": ordered_product.quantity_ordered,
                            "price_at_time": str(ordered_product.order_price),
                            "description": ordered_product.branch_product.product.description,
                            "image": ordered_product.branch_product.product.image
                        }
                        for ordered_product in products_to_use
                    ],
                    "total": str(last_order.transaction.final_total)
                }

                return response
            return None
        except Exception as e:
            raise Exception(f"Failed to get last order: {str(e)}")

    def _get_price_changes(self, last_order, current_products):
        try:
            price_changes = []
            last_order_date = last_order["date"]

            # dictionary of current products
            current_products_dict = {
                str(product["id"]): product
                for product in current_products
            }

            for item in last_order["items"]:
                product_id = str(item["product_id"])
                if product_id in current_products_dict:
                    old_price = float(item["price_at_time"])
                    current_price = float(current_products_dict[product_id]["branch_price"])

                    if old_price != current_price:
                        price_changes.append(
                            {
                                "product_id": product_id,
                                "product_name": item["name"],
                                "old_price": str(old_price),
                                "new_price": str(current_price),
                                "difference": str(round(current_price - old_price, 2)),
                                "percentage_change": round(
                                    ((current_price - old_price) / old_price) * 100, 2
                                ),
                                "image": current_products_dict[product_id]["product"]["photo"],
                            }
                        )

            return price_changes if price_changes else None
        except Exception as e:
            raise Exception(f"Failed to calculate price changes: {str(e)}")

    def _get_branch_products(self, branch):
        bps = branch_productserializer(
            BranchProduct.objects.filter(branch=branch), many=True
        )
        return bps

    def _get_branch_sale_campaigns(self, branch):
        sale_campaigns = SaleCampaign.objects.filter(
            branch=branch, campaign_ends__gte=datetime.datetime.now()
        )
        scs = SaleCampaignSerializer()
        if sale_campaigns:
            scs = SaleCampaignSerializer(sale_campaigns, many=True)
            return sale_campaigns, scs.data
        return None, None

    def _locate_nearest_branch(
        self, coordinates, merchant_business: MerchantBusiness, gmaps_client
    ):
        try:
            # use the coordinates provided to find the nearest branch:
            nearest_branch = googlemaps.places.find_place(
                client=gmaps_client,
                input=merchant_business.name,
                input_type="textquery",
                fields=["formatted_address", "name"],
                location_bias=f"circle:3000@{coordinates}",
            )
            # if the response does not contain any candidates, return an error response:
            if not nearest_branch["candidates"]:
                return {"success": False, "message": "No branches found in Google Maps response"}

            # get the address of the located branch:
            branch_address = nearest_branch["candidates"][0]["formatted_address"]
            normalized_branch_address = " ".join(branch_address.split())

            # in our database, find the branch that matches this address:
            # this must return one, if it does not this is a critical error:
            try:
                branch = Branch.objects.get(
                    address__icontains=normalized_branch_address,
                    merchant__name__icontains=merchant_business.name
                )
            except Exception as e:
                raise Exception(f"Failed to find branch matching address (Critical error): {str(e)}")

            # serialize the branch and get the products:
            bs = BranchSerializer(branch, many=False)
            branch_products = self._get_branch_products(branch)

            #  get the sale campaigns created by this branch:
            sale_campaigns, sale_campaigns_serialized = self._get_branch_sale_campaigns(branch)

            # if sale campaigns have been found we need to adjust the prices in the branch products
            # according to the sale campaign discount percentages:
            self._adjust_prices_based_on_sale_campaigns(
                sale_campaigns, branch_products.data
            )

            # set the branch data response:
            branch_data = {
                "branch": bs.data, 
                "products": branch_products.data,
                "sale_campaigns": sale_campaigns_serialized if sale_campaigns else [],
            }
            return branch_data

        except Exception as e:
            print(f"Error in _find_nearest_branch: {str(e)}")
            return {
                "success": False,
                "message": "Failed to get stores near customer",
                "error": str(e),
            }

    def _adjust_prices_based_on_sale_campaigns(self, sale_campaigns, branch_products):

        # adjust prices for each product if it is on sale:
        if sale_campaigns:
            for branch_product in branch_products:
                sale_campaign = sale_campaigns.filter(branch_product=branch_product["id"]).first()
                if sale_campaign:
                    discount = sale_campaign.percentage_off
                    discounted_price = float(branch_product["branch_price"]) * (1 - discount / 100)
                    branch_product["branch_price"] = str(f"{discounted_price:.2f}")

    def _get_customer_address(self, coordinates, gmaps_client):
        try:
            device_address = googlemaps.geocoding.reverse_geocode(
                gmaps_client,
                coordinates,
            )
            device_address = device_address[0]
            return device_address["formatted_address"]
        except Exception as e:
            raise Exception(f"Failed to get location area: {str(e)}")

    def _set_distance(self, distances, branches):
        for distance_data in distances:
            branches["distance"] = distance_data
        return branches

    def _get_distance(self, coordinates, address, gmaps_client):
        try:
            distances = googlemaps.distance_matrix.distance_matrix(
                client=gmaps_client,
                origins=[coordinates],
                destinations=[address]
            )
            distance = distances["rows"][0]["elements"]
            return distance
        except Exception as e:
            raise Exception(f"Failed to get distance from customer: {str(e)}")


class GetUpdatedMerchantsNearby(APIView, GlobalViewFunctions):

    def get(self, request, **kwargs):
        try:
            logger.info("Getting updated stores near customer...")
            updatedMerchantsNearby = []
            stores = json.loads(kwargs["storeIds"])
            storeIds = [store.get("id") for store in stores]
            storeDistances = [store.get("distance") for store in stores]
            merchants = MerchantBusiness.objects.filter(
                id__in=storeIds)
            for index, merchant in enumerate(merchants):
                products = self.get_products(merchant)
                serializer = MerchantSerializer(merchant, many=False)
                updatedMerchantsNearby.append({
                    "merchant": serializer.data,
                    "products": products,
                    "distance": {"duration": {"text": storeDistances[index]}}
                })
            return Response({
                "success": True,
                "message": "Stores near customer retrieved successfully",
                "petStoresNearby": updatedMerchantsNearby
            }, status=200)
        except Exception as e:
            return Response({
                "success": False,
                "message": "Failed to get stores near customer",
                "error": str(e)
            }, status=401)


class CreateMerchantView(APIView, GlobalViewFunctions):

    def get(self, request, *args, **kwargs):
        pass

    def post(self, request, *args, **kwargs):
        try:
            if self.if_user_is_super_admin(request):
                merchant = self.createMerchant(request.data)
                if merchant:
                    self.notifyAllOfMerchantCreation()
            return Response({
                "success": True,
                "message": "Merchant created successfully",
                "merchant": merchant.data
            }, status=200)
        except Exception as e:
            return Response({
                "success": False,
                "message": "Failed to create merchant",
                "error": str(e)
            }, status=401)

    def createMerchant(self, receivedPayload):
        merchantSerializer = MerchantSerializer(data=receivedPayload)
        if merchantSerializer.is_valid():
            merchant = merchantSerializer.create(validated_data=receivedPayload)
            return MerchantSerializer(merchant, many=False)
        
    def notifyAllOfMerchantCreation(self):
        # TODO: notify all relevant parties of the creation of a new merchant via email:
        pass


class DeactivateMerchantView(APIView, GlobalViewFunctions):

    def get(self, request):
        pass

    def post(self, request):
        try:
            if request.user.useraccount.is_super_user:
                self.deactivateMerchant(request.data["merchantId"])
                self.notifyAllOfDeactivation()
                return Response({
                    "success": True,
                    "message": "merchant deactivated successfully"
                }, status=200)
        except Exception as e:
            return Response({
                "success": False,
                "message": "Failed to deactivate merchant",
                "error": str(e)
            }, status=500)
    
    def deactivateMerchant(self, merchantId):
        merchant = MerchantBusiness.objects.get(pk=int(merchantId))
        merchant.is_active = False
        merchant.save()
        
    def notifyAllOfDeactivation(self):
        # TODO: send emails to relevant parties notifiying them of the deactivation:
        pass


class UpdateMerchant(APIView, GlobalViewFunctions):

    def get(self, request):
        pass

    def post(self, request):
        try:
            if self.if_user_is_super_admin(request):
                updatedMerchant = self.updateMerchant(request)
                merchantSerializer = MerchantSerializer(updatedMerchant, many=False)
                self.notifyAllOfUpdate()
                return Response({
                    "success": True,
                    "message": "Merchant updated successfully",
                    "updatedMerchant": merchantSerializer.data
                }, status=200)
            else: raise Exception(self.exceptionStrings[1])
        except Exception as e:
            return Response({
                "success": False,
                "message": "Failed to deactivate merchant",
                "error": str(e)
            }, status=500)
    
    def updateMerchant(self, request):
        receivedPayload = request.data.copy()
        merchant = MerchantBusiness.objects.get(pk=int(receivedPayload["merchantPk"]))
        del receivedPayload["merchantPk"]
        for key, value in receivedPayload.items():
            self.validateKey(key)
            merchant.__setattr__(key, value)
        merchant.save()
        return merchant
    
    def validateKey(self, key):
        if (key == "fernetToken"):
            raise Exception("FernetToken cannot be modified")
        
    def notifyAllOfUpdate(self):
        # send emails to relevant parties notifiying them of the deactivation:
        pass


class AcknowledgeOrderView(APIView, GlobalViewFunctions):

    def get(self, request, *args, **kwargs):
        try:
            if self.if_user_is_merchant(request):
                orderPk = kwargs["orderPk"]
                order = Order.objects.filter(pk=orderPk).first()
                notificationSent = self.send_notification_of_acknowledgement(order)
                if not notificationSent:
                    self.send_acknowledgement_email(order)
                order.acknowledged = True
                order.save()
            else: raise Exception("You're not permitted to use this feature")
            return Response({
                "message": "Order acknowledged successfully",
                "orderAcknowledged": True,
            }, status=200)
        except Exception as e:
            self.send_acknowledgement_email(order)
            return Response({
                "sucess": False,
                "message": "Failed to acknowledge order",
                "error": str(e)
            }, status=500)
        
    def send_notification_of_acknowledgement(self, order):
        notificationSent = FirebaseInstance().sendOrderAcknowledgementNotification(order)
        return notificationSent
    
    def send_acknowledgement_email(self, order:Order):
        pass


class FulfillOrderView(APIView, GlobalViewFunctions):

    def get(self, request, **kwargs):
        try:
            orderPk = kwargs["orderPk"]
            if self.if_user_is_merchant(request):
                order = self.fulfillOrder(orderPk)
                orderSerializer = OrderSerializer(order, many=False)
            else: raise Exception("You don't have permission to access this feature.")
            return Response({
                "success": True,
                "message": "Order fulfilled successfully",
                "order": orderSerializer.data,
            })
        except Exception as e:
            return Response({
                "success": False,
                "message": "Failed to fulfill order",
                "error": str(e)
            })
        
    def fulfillOrder(self, orderPk):
        order = Order.objects.filter(pk=orderPk).first()
        if order:
            order.status = Order.DELIVERED
            order.save()
            return order
        else: raise Exception("This order was not found")
