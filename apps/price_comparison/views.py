from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from apps.products.models import BranchProduct
from .serializers import BranchProductSerializer

class ProductSearchView(APIView):

    def get(self, request):
        query = request.GET.get('query', '').strip()
        if query:
            # Filter products based on the search query & sort by price
            products = BranchProduct.objects.filter(
                Q(product__name__icontains=query),
                inStock=True,
                isActive=True
            ).order_by('branchPrice')

            serializer = BranchProductSerializer(products, many=True)
            return Response({'products': serializer.data}, status=status.HTTP_200_OK)
        
        return Response({'products': []}, status=status.HTTP_200_OK)

