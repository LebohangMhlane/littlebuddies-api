from django.conf import settings

import json
import googlemaps.addressvalidation
import googlemaps.client
import googlemaps.convert
import googlemaps.distance_matrix
import googlemaps.geocoding
import googlemaps.geolocation
import googlemaps.maps
from rest_framework.views import APIView
from rest_framework.response import Response

import googlemaps

from apps.integrations.firebase_integration.firebase_module import FirebaseInstance
from apps.merchants.models import MerchantBusiness
from apps.merchants.serializers.merchant_serializer import MerchantSerializer

from apps.orders.models import Order
from apps.orders.serializers.order_serializer import OrderSerializer
from global_view_functions.global_view_functions import GlobalViewFunctions
import logging

logger = logging.getLogger(__name__)

class getNewMerchantsNearby(APIView, GlobalViewFunctions):
    def get(self, request, **kwargs):
        try:
            logger.info("Getting stores near customer...")
            # TODO: restrict api key access to server ip address:
            gmaps = googlemaps.Client(key=settings.GOOGLE_SERVICES_API_KEY)
            deviceLocation = kwargs["coordinates"]
            locationArea, customerAddress = self._getLocationArea(deviceLocation, gmaps)
            merchantsNearby = self._getMerchantsNearby(locationArea, deviceLocation, gmaps)
            return Response({
                "success": True,
                "message": "Stores near customer retrieved successfully",
                "petStoresNearby": merchantsNearby,
                "customerAddress": customerAddress
            }, status=200)
        except Exception as e:
            return Response({
                "success": False,
                "message": "Failed to get stores near customer",
                "error": str(e)
            }, status=200)
        
    def _getLocationArea(self, deviceLocation, gmaps):
        logger.info("Getting location area...")
        try:
            locationArea = None
            deviceAddresses = googlemaps.geocoding.reverse_geocode(
                gmaps,
                deviceLocation,
            )
            deviceAddresses = deviceAddresses[0]
            for component in deviceAddresses["address_components"]:
                if component["long_name"] in MerchantBusiness().getLocationsList():
                    locationArea = component["long_name"]
                    break
            return locationArea, deviceAddresses["formatted_address"]
        except Exception as e:
            raise Exception(f"Failed to get location area: {str(e)}")

    def _getMerchantsNearby(self, locationArea, deviceLocation, gmaps):
        logger.info("Getting stores near customer...")
        merchantsNearby = []
            
        def setDistanceData(allDistances):
            for index, distanceData in enumerate(allDistances):
                merchantsNearby[index]["distance"] = distanceData
                continue

        merchantsInArea = MerchantBusiness.objects.filter(
            area=locationArea,
            isActive=True,
        )
        merchantAddresses = []
        if merchantsInArea:
            for merchant in merchantsInArea:
                merchantAddresses.append(merchant.address)
                products = self.getProducts(merchant)
                serializer = MerchantSerializer(merchant, many=False)
                merchantsNearby.append({
                    "merchant": serializer.data,
                    "products": products,
                })
        allDistances = self._getDistanceFromCustomer(deviceLocation, merchantAddresses, gmaps)
        setDistanceData(allDistances)
        return merchantsNearby
    
    def _getDistanceFromCustomer(self, deviceLocation, merchantAddresses, gmaps):
            try:
                distance = googlemaps.distance_matrix.distance_matrix(
                    client=gmaps,
                    origins=[deviceLocation],
                    destinations=merchantAddresses
                )
                distances = distance["rows"][0]["elements"]
                return distances
            except Exception as e:
                raise Exception(f"Failed to get distance from customer: {str(e)}")
    

class getUpdatedMerchantsNearby(APIView, GlobalViewFunctions):

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
                products = self.getProducts(merchant)
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
            if self.checkIfUserIsSuperAdmin(request):
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
        # TODO: notify all relevant parties of the creation of a new merchant:
        pass


class DeactivateMerchantView(APIView, GlobalViewFunctions):

    def get(self, request):
        pass

    def post(self, request):
        try:
            if request.user.useraccount.canCreateMerchants:
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
        merchant.isActive = False
        merchant.save()
        
    def notifyAllOfDeactivation(self):
        # TODO: send emails to relevant parties notifiying them of the deactivation:
        pass


class UpdateMerchant(APIView, GlobalViewFunctions):

    def get(self, request):
        pass

    def post(self, request):
        try:
            if self.checkIfUserIsSuperAdmin(request):
                updatedMerchant = self.updateMerchant(request)
                merchantSerializer = MerchantSerializer(updatedMerchant, many=False)
                self.notifyAllOfUpdate()
                return Response({
                    "success": True,
                    "message": "Merchant updated successfully",
                    "updatedMerchant": merchantSerializer.data
                }, status=200)
            else: raise Exception(self.exceptionString2)
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
            if self.checkIfUserIsMerchant(request):
                orderPk = kwargs["orderPk"]
                order = Order.objects.filter(pk=orderPk).first()
                notificationSent = self.sendNotificationOfOrderAcknowledgement(order)
                if not notificationSent:
                    self.sendAcknowledgementEmail(order)
                order.acknowledged = True
                order.save()
            else: raise Exception("You're not permitted to use this feature")
            return Response({
                "success": True,
                "message": "Order acknowledged successfully",
            }, status=200)
        except Exception as e:
            self.sendAcknowledgementEmail(order)
            return Response({
                "sucess": False,
                "message": "Failed to acknowledge order",
                "error": str(e)
            }, status=500)
        
    def sendNotificationOfOrderAcknowledgement(self, order):
        notificationSent = FirebaseInstance().sendOrderAcknowledgementNotification(order)
        return notificationSent
    
    def sendAcknowledgementEmail(self, order:Order):
        pass


class FulfillOrderView(APIView, GlobalViewFunctions):

    def get(self, request, **kwargs):
        try:
            orderPk = kwargs["orderPk"]
            if self.checkIfUserIsMerchant(request):
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



