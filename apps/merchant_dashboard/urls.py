from django.urls import path
from .views import *

urlpatterns = [
    path('get-merchant-dashboard', ManageOrdersView.as_view(), name='get_merchant_dashboard'),
]
