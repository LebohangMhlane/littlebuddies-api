"""
URL configuration for payfast project.

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
from django.urls import path

from payfast_payments.views import (PaymentSuccessView, 
                                    PaymentInitializationView, 
                                    PaymentCancelledView,
                                    PaymentNotificationView, 
                                    )

urlpatterns = [
    path('admin/', admin.site.urls),
    path('payment/', PaymentInitializationView.as_view(), name="payment_page"),
    path('payment_successful/', PaymentSuccessView.as_view(), name="payment_successful_page"),
    path('payment_cancelled/', PaymentCancelledView.as_view(), name="payment_cancelled_page"),
    path('payment_notification/', PaymentNotificationView.as_view(), name="payment_notification_page"),
]
