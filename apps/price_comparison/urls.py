from django.urls import path
from .views import ProductSearchView

urlpatterns = [
    path('<str:query>', ProductSearchView.as_view(), name='search_products'),
]
