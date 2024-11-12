from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from apps.products.models import BranchProduct
from apps.products.serializers.serializers import BranchProductSerializer
from global_view_functions.global_view_functions import GlobalViewFunctions

class ProductSearchView(APIView, GlobalViewFunctions):
    permission_classes = []

    def get(self, request, **kwargs):
        try:

            # prepare query parameters:
            query = kwargs["query"]
            store_ids = kwargs["store_ids"].split(",")

            # fail the endpoint if there is no query:
            if not query or len(query.strip()) == 0:
                raise Exception("A search query was not specified")

            # find the products related to the query:
            products = BranchProduct.objects.select_related(
                'product',
                'branch', 
                'branch__merchant'
            ).filter(
                Q(product__name__icontains=query) & 
                Q(branch__merchant__id__in=store_ids),  
                inStock=True,
                isActive=True
            )

            # if there are no products then raise exception:
            if not products.exists():
                raise Exception("No product matching this criteria was found")

            # order the products by price:
            products = products.order_by('branchPrice').distinct()

            # serialize the products:
            serializer = BranchProductSerializer(products, many=True)
            
            # return the response:
            return Response({
                "success": True,
                "message": "Products retrieved successfully",
                'products': serializer.data,
                'metadata': {
                    'total_count': products.count(),
                    'filtered_stores': store_ids if store_ids else 'all'
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "success": False,
                "message": "Failed to retrieve products",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)