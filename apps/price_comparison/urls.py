from django.urls import path
from .views import ProductSearchView

urlpatterns = [
    path('search/', ProductSearchView.as_view(), name='search_products'),
]
