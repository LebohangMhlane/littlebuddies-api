from django.urls import path

from apps.products.views import CreateProductView



urlpatterns = [
    path('create-product/', CreateProductView.as_view(), name="create_product_view"),
]
