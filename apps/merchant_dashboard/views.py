from django.shortcuts import render

from django.views import View
from rest_framework.authtoken.models import Token
from apps.merchants.models import Branch, SaleCampaign
from apps.orders.models import Order
from apps.products.models import BranchProduct
from global_view_functions.global_view_functions import GlobalViewFunctions


class ManageBranchView(GlobalViewFunctions, View):

    def get(self, request, *args, **kwargs):
        try:
            # determine what permissions a user has,
            # either global access to all branches or
            # access to only one branch:
            user = self.manually_authenticate_user(request)
            user_account = user.useraccount

            # determine user permission and get the branch:
            branch = self.determine_permission_and_return_branch(
                user_account, kwargs["branch_id"]
            )

            '''These may require pagination'''

            # get branch orders:
            all_branch_orders = Order.objects.filter(transaction__branch=branch)

            # get all current branch products:
            all_branch_products = BranchProduct.objects.filter(branch=branch)

            # get all current sale campaigns:
            all_sale_campaigns = SaleCampaign.objects.filter(branch=branch)

            # return a response:
            context = {}

            return render(
                request,
                "merchant_dashboard_templates/dashboard_homepage.html",
                context,
                status=200,
            )
        except Exception as e:

            # returnable values:
            status = 500
            error = e.args[0]
            error_texts = [
                "You do not have permission to manage this branch",
                "User is not authenticated",
            ]

            # determine the status to return:
            if error in error_texts: status = 403

            context = {}

            # return a response:
            return render(
                request,
                "merchant_dashboard_templates/dashboard_homepage.html",
                context,
                status=status,
            )

    def post(self, request, *args, **kwargs):
        pass

    def manually_authenticate_user(self, request):
        try:
            """
            since we are using normal django view we don't have the luxury of
            rest frameworks automatic authentication service
            """

            # determine if there is a token available:
            if request.headers and request.headers.get("Authorization"):
                token = request.headers.get("Authorization").split(" ")[1]
                token_instance = Token.objects.filter(key=token)

                # if there is one the return the user associated with it:
                if token_instance:
                    return token_instance.first().user
                else:
                    raise Exception("User is not authenticated")
        except Exception as e:
            raise Exception(e.args[0])

    def determine_permission_and_return_branch(self, user_account, branch_id):
        try:
            # get the branch being managed:
            branch = Branch.objects.get(id=branch_id)

            # check user permissions:
            if user_account.is_merchant:
                if branch in user_account.permitted_branches.all():

                    # return the branch if the user is permitted to access it:
                    return branch
                else:
                    raise Exception("You do not have permission to manage this branch")
        except Exception as e:
            raise Exception(e.args[0])
