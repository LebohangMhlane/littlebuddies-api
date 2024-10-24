from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.db.models import Q
from apps.products.models import BranchProduct
from apps.products.serializers.serializers import BranchProductSerializer
# from .serializers import BranchProductSerializer
from global_view_functions.global_view_functions import GlobalViewFunctions

class ProductSearchView(APIView, GlobalViewFunctions):
    permission_classes = []

    def get(self, request):
        try:
            query = request.GET.get('query', '').strip()
            if query:
                products = BranchProduct.objects.filter(
                    Q(product__name__icontains=query),
                    inStock=True,
                    isActive=True
                ).order_by('branchPrice')
                if products:
                    serializer = BranchProductSerializer(products, many=True)
                    return Response({
                        "success": True,
                        "message": "Products retrieved successfully",
                        'products': serializer.data,
                    }, status=status.HTTP_200_OK)
                else:
                    raise Exception("No product matching this criteria was found")
            else: 
                raise Exception("A search query was not specified")
        except Exception as e:
            return Response({
                "success": False,
                "message": "Failed to retrieve products",
                "error": e.args[0]
            }, status=500)
