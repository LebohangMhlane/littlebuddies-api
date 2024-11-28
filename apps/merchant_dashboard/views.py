from django.shortcuts import render

from django.views import View
from global_view_functions.global_view_functions import GlobalViewFunctions


class ManageOrdersView(View, GlobalViewFunctions):

    def get(self, request, *args, **kwargs):

        try:
            # determine what permissions a user has,
            # either global access to all branches or 
            # access to only one branch:
            user_account = request.user.useraccount

            pass
        except Exception as e:
            context = {}
            return render(request, "", context)

    def post(self, request, *args, **kwargs):
        pass


    def determine_permissions(user_account):
        if user_account.is_merchant:
            pass