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
            query = kwargs["query"]
            store_ids = eval(kwargs["store_ids"])

            if not query:
                raise Exception("A search query was not specified")

            products = BranchProduct.objects.select_related(
                'product',
                'branch', 
                'branch__merchant'
            ).filter(
                Q(product__name__icontains=query),  
                branch__merchant__id__in=store_ids,
                inStock=True,
                isActive=True
            )

            products = products.order_by('branchPrice').distinct()

            if not products.exists():
                raise Exception("No product matching this criteria was found")

            serializer = BranchProductSerializer(products, many=True)
            
            return Response({
                "success": True,
                "message": "Products retrieved successfully",
                'products': serializer.data,
                'metadata': {
                    'total_count': products.count(),
                    'filtered_stores': store_ids if store_ids else 'all'
                }
            }, status=status.HTTP_200_OK)
            
        except ValueError:
            return Response({
                "success": False,
                "message": "Failed to retrieve products",
                "error": "Invalid store IDs format"
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "success": False,
                "message": "Failed to retrieve products",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)