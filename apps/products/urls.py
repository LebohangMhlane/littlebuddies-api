from django.urls import path

from apps.products.views import CreateProductView, DeleteProductView



urlpatterns = [
    path('create-product/', CreateProductView.as_view(), name="create_product_view"),
    path('delete-product/<int:productPk>', DeleteProductView.as_view(), name="delete_product_view"),
]
