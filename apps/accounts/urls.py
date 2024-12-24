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

from apps.accounts import views

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path(
        "create-account/", views.RegistrationView.as_view(), name="create_account_view"
    ),
    path(
        "activate-account/<uidb64>/<activationToken>/",
        views.ActivateAccountView.as_view(),
        name="activate_account_view",
    ),
    path(
        "check-account-activation/",
        views.CheckAccountActivation.as_view(),
        name="check_account_activation_view",
    ),
    path(
        "resend-activation-email/",
        views.ResendActivationEmail.as_view(),
        name="resend_activation_email",
    ),
    path(
        "update-account/", views.UpdateAccountView.as_view(), name="update_account_view"
    ),
    path(
        "deactivate-account/",
        views.DeactivateAccountView.as_view(),
        name="deactivate_account_view",
    ),
    path(
        "password-reset-request/<str:email>",
        views.RequestPasswordReset.as_view(),
        name="password_reset_request_view",
    ),
    path(
        "password-reset/<uidb64>/<resetToken>/",
        views.RequestSubmitPasswordResetForm.as_view(),
        name="password_reset_view",
    ),
    path(
        "get-save-account-settings/",
        views.AccountSettingsView.as_view(),
        name="account_settings_view",
    ),
    path(
        "request-data-copy/", views.DataRequestView.as_view(), name="request_data_copy"
    ),
    path("update-address/", views.UpdateAddressView.as_view(), name="update-address"),
    path("update-address/<str:query>/", views.UpdateAddressView.as_view(), name="update-address"),
]
