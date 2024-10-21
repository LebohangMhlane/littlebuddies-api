from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.db.models import Q
from apps.products.models import BranchProduct
from .serializers import BranchProductSerializer
from global_view_functions.global_view_functions import GlobalViewFunctions

class ProductSearchView(APIView, GlobalViewFunctions):

    permission_classes = []

    def get(self, request):
        query = request.GET.get('query', '').strip()

        # TODO: implement pagination (10):

        if query:
            # Filter products based on the search query & sort by price
            products = BranchProduct.objects.filter(
                Q(product__name__icontains=query),
                inStock=True,
                isActive=True
            ).order_by('branchPrice') #we might need to use(-'branchPrice')

            # TODO: add branch id and return it included in the results "branch_id"

            serializer = BranchProductSerializer(products, many=True)
            return Response({'products': serializer.data}, status=status.HTTP_200_OK)
        
        return Response({'products': []}, status=status.HTTP_200_OK)

