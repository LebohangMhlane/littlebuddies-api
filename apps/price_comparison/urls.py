from django.urls import path
from .views import ProductSearchView

urlpatterns = [
    path('<str:query>/<str:store_ids>', ProductSearchView.as_view(), name='search_products'),
]
