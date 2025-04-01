"""
URL configuration for littlebuddies project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
""" 

from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
import custom_admin_site

urlpatterns = [
    path("admin/", custom_admin_site.custom_admin_site.urls),
    path("accounts/", include("apps.accounts.urls"), name="account_urls"),
    path("merchants/", include("apps.merchants.urls"), name="merchant_urls"),
    path("products/", include("apps.products.urls"), name="product_urls"),
    path("orders/", include("apps.orders.urls"), name="order_urls"),
    path("transactions/", include("apps.transactions.urls"), name="transaction_urls"),
    path(
        "price_comparison/",
        include("apps.price_comparison.urls"),
        name="price_comparison_urls",
    ),
    path("discounts/", include("apps.discounts.urls"), name="discount"),
    path(
        "merchant_dashboard/",
        include("apps.merchant_dashboard.urls"),
        name="merchant_dashboard",
    ),
    path(
        "paystack/",
        include("apps.paystack.urls"),
        name="paystack",
    ),
    path(
        "app_manager/",
        include("apps.app_manager.urls"),
        name="app_manager",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_URL)
