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
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from  django.conf.urls.static import static 

from apps.paygate.views import (PaymentSuccessView, 
                                PaymentInitializationView, 
                                PaymentCancelledView,
                                PaymentNotificationView, 
                                )

urlpatterns = [
    path('admin/', admin.site.urls),
    path('initiate_payment/', PaymentInitializationView.as_view(), name="initiate_payment_view"),
    path('payment_successful/', PaymentSuccessView.as_view(), name="payment_successful_view"),
    path('payment_cancelled/', PaymentCancelledView.as_view(), name="payment_cancelled_view"),
    path('payment_notification/', PaymentNotificationView.as_view(), name="payment_notification_view"),
    path("accounts/", include("apps.accounts.urls"), name="account_urls"),
    path("merchants/", include("apps.merchants.urls"), name="merchant_urls"),
    path('products/', include("apps.products.urls"), name="product_urls"),
    path('orders/', include("apps.orders.urls"), name="order_urls"),
    path('transactions/', include("apps.transactions.urls"), name="transaction_urls"),
    path('search/', include("apps.price_comparison.urls"), name="price_comparison_urls"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root = settings.STATIC_URL)
