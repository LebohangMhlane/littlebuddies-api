from django.contrib.admin import AdminSite

from apps.accounts.models import UserAccount


class CustomAdminSite(AdminSite):

    site_header = ("Littlebuddies Management Dashboard")  
    site_title = "Management Dashboard"  
    index_title = "Welcome to Littlebuddies"  

    def set_models_to_hide(self):
        return []

    def user_is_superuser(self, request):
        if not request.user.is_anonymous:
            return request.user.is_superuser

    def user_is_merchant(self, request):
        if not request.user.is_anonymous:
            return request.user.useraccount.is_merchant

    def hide_models_from_merchants(self, filtered_app_list):
        for app in filtered_app_list:
            app["models"] = [
                app_model
                for app_model in app["models"]
                if app_model["object_name"] not in self.set_models_to_hide()
            ]
        return filtered_app_list

    def hide_apps_from_merchants(self, app_list):
        apps_to_hide = ["accounts", "authtoken", "auth"]
        filtered_app_list = [
            app for app in app_list if app["app_label"] not in apps_to_hide
        ]
        return filtered_app_list

    def create_account_for_superuser(self, request):
        user_is_superuser = request.user.is_superuser
        if user_is_superuser and not UserAccount.objects.filter(user=request.user).exists():
            UserAccount.objects.create(user=request.user, device_token="fakedevicetoken")

    def get_app_list(self, request):
        self.create_account_for_superuser(request)
        app_list = super().get_app_list(request)
        if not request.path.startswith('/admin/login/'):
            if self.user_is_merchant(request):
                filtered_app_list = self.hide_apps_from_merchants(app_list)
                filtered_app_and_models_list = self.hide_models_from_merchants(filtered_app_list)
                return filtered_app_and_models_list
            if self.user_is_superuser(request):
                return app_list
            raise Exception("You are not authorized to access this site.")
        else:
            return app_list

custom_admin_site = CustomAdminSite(name="Littlebuddies Admin")
