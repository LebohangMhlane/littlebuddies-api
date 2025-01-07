from django.contrib.admin import AdminSite


class CustomAdminSite(AdminSite):

    def set_apps_to_hide(self):
        return ["accounts"]

    def set_models_to_hide(self):
        return []

    def user_is_superuser(self, request):
        return request.user.is_superuser

    def user_is_merchant(self, request):
        # return request.user.useraccount.is_merchant
        return True

    def hide_models_from_merchants(self, filtered_app_list):
        for app in filtered_app_list:
            app["models"] = [
                app_model
                for app_model in app["models"]
                if app_model["object_name"] not in self.set_models_to_hide()
            ]
        return filtered_app_list

    def hide_apps_from_merchants(self, app_list):
        apps_to_hide = self.set_apps_to_hide()
        filtered_app_list = [
            app for app in app_list if app["app_label"] not in apps_to_hide
        ]
        return filtered_app_list

    def get_app_list(self, request):
        app_list = super().get_app_list(request)
        if self.user_is_merchant(request):
            filtered_app_list = self.hide_apps_from_merchants(app_list)
            filtered_app_and_models_list = self.hide_models_from_merchants(filtered_app_list)
            return filtered_app_and_models_list
        if self.user_is_superuser():
            return app_list
        raise Exception("You are not authorized to access this site.")

custom_admin_site = CustomAdminSite(name="Littlebuddies Admin")
