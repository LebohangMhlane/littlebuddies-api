from django.urls import path
from apps.merchants.views import (CreateMerchantView, 
                                DeactivateMerchantView, GetStoreRange,
                                UpdateMerchant,
                                AcknowledgeOrderView,
                                FulfillOrderView,
                                GetNearestBranch,
                                GetUpdatedMerchantsNearby
                                )

urlpatterns = [

    # little buddies unique url name urls:
    path('get-store-range/', GetStoreRange.as_view(), name="get_store_range"),
    path('get-nearest-branch/<str:coordinates>/<int:merchantId>', GetNearestBranch.as_view(), name="get_nearest_branch"),
    path('get-updated-petstores-near-me/<str:storeIds>/', GetUpdatedMerchantsNearby.as_view(), name="get_updated_petstores_near_me"),


    # dynamic name urls:
    path('create-merchant/', CreateMerchantView.as_view(), name="create_merchant_view"),
    path('deactivate-merchant/', DeactivateMerchantView.as_view(), name="deactivate_merchant_view"),
    path('update-merchant/', UpdateMerchant.as_view(), name="update_merchant_view"),
    path('acknowledge-order/<int:orderPk>/', AcknowledgeOrderView.as_view(), name="acknowledge_order_view"),
    path('fulfill-order/<int:orderPk>/', FulfillOrderView.as_view(), name="fulfill_order_view"),
]

