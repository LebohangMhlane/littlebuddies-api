from django.conf import settings

import json

import traceback

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

from apps.orders.models import Order
from apps.orders.serializers.order_serializer import OrderSerializer
from apps.products.serializers.serializers import BranchProductSerializer, ProductSerializer
from global_view_functions.global_view_functions import GlobalViewFunctions
import logging

logger = logging.getLogger(__name__)

class GetStoreRange(APIView, GlobalViewFunctions):
    
    def get(self, request, **kwargs):
        try:
            coordinates = kwargs.get('coordinates')
            mb = MerchantBusiness.objects.all()
            sc = SaleCampaign.objects.filter(branch__merchant__in=mb)
            saleCampaigns = []
            if sc: scs = SaleCampaignSerializer(sc, many=True) 
            saleCampaigns = scs.data
            if mb: ms = MerchantSerializer(mb, many=True)
            else: raise Exception("No Pet stores were found")
            return Response({
                "success": True,
                "message": "Store range retrieved successfully",
                "petstores": ms.data,
                "saleCampaigns": saleCampaigns
            }, status=200)
        except Exception as e:
            return Response({
                "success": False,
                "message": "Failed to get stores near customer",
                "error": str(e)
            }, status=200)


class GetNearestBranch(APIView, GlobalViewFunctions):

    def get(self, request, **kwargs):
        try:
            # TODO: restrict api key access to server ip address:
            coordinates = kwargs["coordinates"]
            merchantBusiness = MerchantBusiness.objects.get(id=kwargs["merchantId"])
            gmapsClient = googlemaps.Client(key=settings.GOOGLE_SERVICES_API_KEY)
            customerAddress = self._getCustomerAddress(coordinates, gmapsClient)
            branchData = self._findNearestBranch(
                coordinates, merchantBusiness.name, gmapsClient)
            distanceFromBranch = self._getDistance(
                coordinates, branchData["branch"]["address"], gmapsClient)
            self._setDistance(distanceFromBranch, branchData)
            return Response({
                "success": True,
                "message": "Nearest branch retrieved successfully",
                "nearestBranch": branchData,
                "customerAddress": customerAddress
            }, status=200)
        except Exception as e:
            return Response({
                "success": False,
                "message": "Failed to get stores near customer",
                "error": str(e)
            }, status=200)
    
    def _findNearestBranch(self, coordinates, merchantName, gmapsClient):
        try:
            nearestBranch = googlemaps.places.find_place(
                client=gmapsClient,
                input=merchantName,
                input_type="textquery",
                fields=["formatted_address","name"],
                location_bias=f"circle:3000@{coordinates}"
            )
            branchAddress = nearestBranch["candidates"][0]["formatted_address"]
            branchData = {}
            branch = Branch.objects.get(address__startswith=branchAddress)
            bps = BranchProductSerializer(branch.branchproduct_set, many=True)
            bs = BranchSerializer(branch, many=False)
            scs = SaleCampaignSerializer()
            saleCampaigns = SaleCampaign.objects.filter(branch=branch)
            if saleCampaigns: scs = SaleCampaignSerializer(saleCampaigns, many=True)
            branchData = {
                "branch": bs.data,
                "products": bps.data,
                "saleCampaigns": scs.data if saleCampaigns else [],
            }
            return branchData
        except Exception as e:
            raise Exception(f"No branch could be found for this store: {str(e)} - {branchAddress}")
            
    def _getCustomerAddress(self, coordinates, gmapsClient):
        try:
            deviceAddresses = googlemaps.geocoding.reverse_geocode(
                gmapsClient,
                coordinates,
            )
            deviceAddress = deviceAddresses[0]
            return deviceAddress["formatted_address"]
        except Exception as e:
            raise Exception(f"Failed to get location area: {str(e)}")

    def _setDistance(self, distances, branches):
        for distanceData in distances:
            branches["distance"] = distanceData
        return branches
        
    def _getDistance(self, coordinates, address, gmapsClient):
        try:
            distances = googlemaps.distance_matrix.distance_matrix(
                client=gmapsClient,
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
        # TODO: notify all relevant parties of the creation of a new merchant via email:
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
                "message": "Order acknowledged successfully",
                "orderAcknowledged": True,
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



