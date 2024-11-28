from django.shortcuts import render

from django.views import View
from rest_framework.authtoken.models import Token
from apps.merchants.models import Branch
from global_view_functions.global_view_functions import GlobalViewFunctions


class ManageOrdersView(GlobalViewFunctions, View):

    def get(self, request, *args, **kwargs):
        try:
            # determine what permissions a user has,
            # either global access to all branches or 
            # access to only one branch:
            user = self.manually_authenticate_user(request)
            user_account = user.useraccount

            # get the branch being managed:
            branch_id = kwargs["branch_id"]
            branch = Branch.objects.get(id=branch_id)

            pass
        except Exception as e:
            context = {}
            return render(request, "", context)

    def post(self, request, *args, **kwargs):
        pass

    def manually_authenticate_user(self, request):

        '''
        since we are using normal django view we don't have the luxury of
        rest frameworks automatic authentication service
        '''

        # determine if there is a token available:
        if request.headers and request.headers.get('Authorization'):
            token = request.headers.get('Authorization').split(" ")[1]
            token_instance = Token.objects.filter(key=token)
            
            # if there is one the return the user associated with it:
            if token_instance: return token_instance.first().user
            else: raise Exception("Authentication failed!")

    def determine_permissions(user_account):
        if user_account.is_merchant:
            pass