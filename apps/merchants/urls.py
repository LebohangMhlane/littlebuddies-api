from django.urls import path
from apps.merchants.views import (CreateMerchantView, 
                                DeactivateMerchantView,
                                UpdateMerchant,
                                AcknowledgeOrderView,
                                FulfillOrderView,
                                getBranchesNearby,
                                getUpdatedMerchantsNearby
                                )

urlpatterns = [

    # little buddies unique url name urls:
    path('get-petstores-near-me/<str:coordinates>/', getBranchesNearby.as_view(), name="get_petstores_near_me"),
    path('get-updated-petstores-near-me/<str:storeIds>/', getUpdatedMerchantsNearby.as_view(), name="get_updated_petstores_near_me"),


    # dynamic name urls:
    path('create-merchant/', CreateMerchantView.as_view(), name="create_merchant_view"),
    path('deactivate-merchant/', DeactivateMerchantView.as_view(), name="deactivate_merchant_view"),
    path('update-merchant/', UpdateMerchant.as_view(), name="update_merchant_view"),
    path('acknowledge-order/<int:orderPk>/', AcknowledgeOrderView.as_view(), name="acknowledge_order_view"),
    path('fulfill-order/<int:orderPk>/', FulfillOrderView.as_view(), name="fulfill_order_view"),
]

