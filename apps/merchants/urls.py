from django.urls import path

from apps.merchants.views import (CreateMerchantView, 
                                DeactivateMerchantView,
                                CreateProductView)

urlpatterns = [
    path('create-merchant/', CreateMerchantView.as_view(), name="create_merchant_view"),
    path('deactivate-merchant/', DeactivateMerchantView.as_view(), name="deactivate_merchant_view"),
    path('create-product/', CreateProductView.as_view(), name="create_product_view"),
]
