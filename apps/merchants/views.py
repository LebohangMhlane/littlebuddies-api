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
from apps.products.models import Product
from apps.products.serializers.serializers import ProductSerializer
from global_view_functions.global_view_functions import GlobalViewFunctions


class getMerchantsNearby(APIView, GlobalViewFunctions):
    def get(self, request, **kwargs):
        try:
            # TODO: restrict api key access to server ip address:
            gmaps = googlemaps.Client(key="AIzaSyBQgPeIoIWjNxRWzwKoLJhHO5yUyUcTLXo")
            deviceLocation = kwargs["coordinates"]
            locationArea = self._getLocationArea(deviceLocation, gmaps)
            merchantsNearby = self._getMerchantsNearby(locationArea, deviceLocation, gmaps)
            return Response({
                "success": True,
                "message": "Stores near customer retrieved successfully",
                "petStoresNearby": merchantsNearby
            }, status=200)
        except Exception as e:
            return Response({
                "success": False,
                "message": "Failed to get stores near customer",
                "error": str(e)
            }, status=401)
        
    def _getLocationArea(self, deviceLocation, gmaps):
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
            return locationArea
        except Exception as e:
            raise Exception(f"Failed to get location area: {str(e)}")

    def _getMerchantsNearby(self, locationArea, deviceLocation, gmaps):
        merchantsNearby = []

        def getProducts(merchant):
            products = Product.objects.filter(
                isActive=True,
                merchant=merchant,
                inStock=True,
            )
            if products:
                serializer = ProductSerializer(products, many=True)
            return serializer.data
        def getDistancesFromCustomer(deviceLocation, merchantAddresses):
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
                products = getProducts(merchant)
                serializer = MerchantSerializer(merchant, many=False)
                merchantsNearby.append({
                    "merchant": serializer.data,
                    "products": products,
                })
        allDistances = getDistancesFromCustomer(deviceLocation, merchantAddresses)
        setDistanceData(allDistances)
        
        return merchantsNearby



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



