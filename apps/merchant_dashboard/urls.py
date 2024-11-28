from django.urls import path
from .views import ProductSearchView

urlpatterns = [
    path('get-merchant-dashboard', ProductSearchView.as_view(), name='get_merchant_dashboard'),
]
