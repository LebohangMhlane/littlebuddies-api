from django.urls import path

from apps.app_manager.views import AppManagerView

urlpatterns = [
    path("get-app-manager/", AppManagerView.as_view(), name="get_app_manager"),
]
