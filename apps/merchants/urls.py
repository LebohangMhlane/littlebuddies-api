from django.urls import path
from apps.merchants.views import (CreateMerchantView, 
                                DeactivateMerchantView,
                                UpdateMerchant
                                )

urlpatterns = [
    path('create-merchant/', CreateMerchantView.as_view(), name="create_merchant_view"),
    path('deactivate-merchant/', DeactivateMerchantView.as_view(), name="deactivate_merchant_view"),
    path('update-merchant/', UpdateMerchant.as_view(), name="update_merchant_view"),
]

