from django.urls import path
from .views import ReferralView, ClaimVoucherView

urlpatterns = [
    path('api/refer/', ReferralView.as_view(), name='refer-friend'),
    path('api/claim-voucher/', ClaimVoucherView.as_view(), name='claim-voucher'),
]
