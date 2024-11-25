from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
from django.db.models import F, Case, When, DecimalField, Q, Exists, OuterRef, Subquery

from apps.products.models import BranchProduct
from apps.merchants.models import SaleCampaign
from apps.products.serializers.serializers import BranchProductSerializer
from global_view_functions.global_view_functions import GlobalViewFunctions

class ProductSearchView(APIView, GlobalViewFunctions):
    permission_classes = []

    def get(self, request, **kwargs):
        try:
            # Extract query parameters
            query = kwargs.get("query", "").strip()
            store_ids = kwargs.get("store_ids", "").split(",")
            
            # Validate and parse store_ids
            try:
                if not isinstance(store_ids, list):
                    raise ValueError("Store IDs should be a list.")
            except (SyntaxError, ValueError) as ex:
                raise Exception("Invalid store IDs format. Ensure it's a list.")

            if not query:
                raise Exception("A search query was not specified.")

            # Prepare filters and current date
            current_date = datetime.now().date()
            filters = Q(product__name__icontains=query, inStock=True, isActive=True)
            
            if store_ids:
                filters &= Q(branch__merchant__id__in=store_ids)

            # Query branch products
            products = BranchProduct.objects.select_related(
                'product', 'branch', 'branch__merchant'
            ).filter(filters)

            if not products.exists():
                raise Exception("No product matching this criteria was found.")

            # Query for active campaigns
            active_campaigns = SaleCampaign.objects.filter(
                campaignEnds__gte=current_date,
                branchProducts=OuterRef('pk')
            ).order_by('id') 

            products = products.annotate(
                has_campaign=Exists(active_campaigns),
                campaign_percentage=Subquery(
                    active_campaigns.values('percentageOff')[:1],
                    output_field=DecimalField(max_digits=10, decimal_places=2)
                ),
                final_price=Case(
                    When(
                        has_campaign=True,
                        then=F('branchPrice') - (F('branchPrice') * F('campaign_percentage') / 100)
                    ),
                    default=F('branchPrice'),
                    output_field=DecimalField(max_digits=10, decimal_places=2)
                )
            )

            serializer = BranchProductSerializer(products, many=True)
            serialized_data = serializer.data

            # Add campaign details to serialized data
            for product_data, product in zip(serialized_data, products):
                if product.has_campaign:
                    product_data['campaign'] = {
                        'percentage_off': float(product.campaign_percentage or 0),
                        'final_price': float(product.final_price or product.branchPrice)
                    }
                else:
                    product_data['campaign'] = None

            return Response({
                "success": True,
                "message": "Products retrieved successfully.",
                "products": serialized_data,
                "metadata": {
                    "total_count": len(serialized_data),
                    "query": query,
                    "filtered_stores": store_ids or "all",
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "success": False,
                "message": "Failed to retrieve products.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
