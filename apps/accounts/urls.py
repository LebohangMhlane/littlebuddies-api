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
from django.urls import path

from apps.accounts.views import (
    RegistrationView, DeactivateAccountView, UpdateAccountView, LoginView)

urlpatterns = [
    path('login/', LoginView.as_view(), name="login"),
    path('create-account/', RegistrationView.as_view(), name="create_account_view"),
    path('update-account/', UpdateAccountView.as_view(), name="update_account_view"),
    path('deactivate-account/', DeactivateAccountView.as_view(), name="deactivate_account_view"),
]
