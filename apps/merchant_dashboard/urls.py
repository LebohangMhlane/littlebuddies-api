from django.urls import path
from .views import *

urlpatterns = [
    path('get-merchant-dashboard/<int:branch_id>', ManageOrdersView.as_view(), name='get_merchant_dashboard'),
]
