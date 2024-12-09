from django.utils import timezone
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import render, redirect
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from rest_framework import status, permissions

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken

from apps.accounts.models import AccountSetting, DataRequest, UserAccount
from apps.accounts.serializers.account_settings_serializer import AccountSettingsSerializer
from apps.accounts.serializers.user_account_serializer import UserAccountSerializer, AddressUpdateSerializer
from apps.accounts.serializers.user_serializer import UserSerializer
from apps.accounts.tokens import accountActivationTokenGenerator

from apps.merchants.models import Branch, MerchantBusiness
from apps.orders.models import Order
from apps.transactions.models import Transaction
from global_serializer_functions.global_serializer_functions import SerializerFunctions
from global_view_functions.global_view_functions import GlobalViewFunctions


class LoginView(ObtainAuthToken, GlobalViewFunctions):

    permission_classes = []

    def post(self, request, *args, **kwargs):
        try:
            user = User.objects.get(email=request.data["email"])
            if user.check_password(request.data["password"]):
                authToken = Token.objects.get(user=user)
                user_account = UserAccount.objects.get(user=user)
                user_accountSerializer = UserAccountSerializer(user_account, many=False)
                self._saveDeviceToken(user, request, user_account)
            else:
                raise Exception("Invalid username or password")
            return Response(
                {"token": authToken.key, "userProfile": user_accountSerializer.data}
            )
        except Exception as e:
            error = e.args[0]
            if "User matching query does not exist" in error:
                e = "No user with that email address was found"
            return Response(
                {"message": "Failed to authenticate user", "error": str(e)}, status=401
            )

    def _saveDeviceToken(self, user, request, user_account):
        if "deviceToken" in request.data:  # only for test cases:
            user_account.deviceToken = request.data["deviceToken"]
        user_account.save()


class RegistrationView(APIView, GlobalViewFunctions, SerializerFunctions):

    permission_classes = []

    def get(self, request, *args, **kwargs):
        pass

    def post(self, request, *args, **kwargs):
        user_account = None
        try:
            user_account = self._start_registration_process(receivedData=request.data)
            authToken = Token.objects.get(user__id=user_account["user"]["id"])
            self.send_activation_email(user_account, request)
            return Response(
                {
                    "success": True,
                    "message": "Account created successfully",
                    "user_account": user_account,
                    "loginToken": authToken.key,
                }
            )
        except Exception as e:
            exception = e.args[0]
            displayableException = self.determine_exception(exception)
            return Response(
                {
                    "success": False,
                    "message": "Failed to create account",
                    "error": displayableException
                },
                status=500,
            )

    def determine_exception(self, exception):
        default = "An error has occured. We are looking into it"
        possible_errors = ["UNIQUE", "Invalid phone number"]
        displayable_errors = [
            "A user with these details already exists",
            "Invalid phone number",
        ]
        for index, possible_error in enumerate(possible_errors):
            if possible_error in exception:
                displayable_error = displayable_errors[index]
                return displayable_error
        return default

    def _start_registration_process(self, receivedData=dict) -> dict:
        user_data, user_account_data = self.sort_user_data(receivedData)
        user_serializer = UserSerializer(data=receivedData)

        if user_serializer.is_valid():
            with transaction.atomic():
                user_instance = user_serializer.create(validated_data=user_data)
                if user_instance:
                    user_account = self.create_user_account(user_account_data, user_instance)
                    user_account = UserAccountSerializer(user_account, many=False)
                    if user_account:
                        user_account_settings = AccountSetting()
                        user_account_settings.user_account = user_account.instance
                        user_account_settings.full_name = user_instance.get_full_name()
                        user_account_settings.save()

                    return user_account.data

    def sort_user_data(self, receivedPayload):
        userData = {
            "username": f"{receivedPayload['firstName']}{receivedPayload['lastName']}{receivedPayload['phoneNumber']}",
            "password": receivedPayload["password"],
            "firstName": receivedPayload["firstName"],
            "lastName": receivedPayload["lastName"],
            "email": receivedPayload["email"],
        }
        user_accountData = {
            "deviceToken": (
                receivedPayload["deviceToken"]
                if "deviceToken" in receivedPayload
                else ""
            ),
            "phoneNumber": receivedPayload["phoneNumber"],
        }
        return userData, user_accountData

    def create_user_account(self, user_account_data, user_instance):
        user_account_data["user"] = user_instance
        user_account_serializer = UserAccountSerializer(data=user_account_data)
        if user_account_serializer.is_valid(raise_exception=True):
            user_account = user_account_serializer.create(validated_data=user_account_data)
            return user_account


class ResendActivationEmail(APIView, GlobalViewFunctions, SerializerFunctions):

    def get(self, request, **kwargs):
        try:
            user_account = UserAccountSerializer(request.user.useraccount)
            self.send_activation_email(user_account.data, request)
            return Response(
                {
                    "message": "Activation email sent successfully",
                    "activationEmailSent": True,
                }
            )
        except Exception as e:
            return Response(
                {
                    "message": "Failed to send activation email",
                    "activationEmailSent": False,
                }
            )


class CheckAccountActivation(APIView, GlobalViewFunctions, SerializerFunctions):

    def get(self, request, **kwargs):
        user_account = request.user.useraccount
        if user_account.emailVerified:
            return Response({"message": "Account activated.", "accountActivated": True})
        else:
            return Response(
                {
                    "message": "Your account is not activated.",
                    "accountActivated": False,
                },
                status=200,
            )


class ActivateAccountView(APIView, GlobalViewFunctions, SerializerFunctions):

    permission_classes = []

    def get(self, request, **kwargs):
        try:
            pk = force_str(urlsafe_base64_decode(kwargs["uidb64"]))
            activationToken = kwargs["activationToken"]
            user = User.objects.get(pk=pk)
            if accountActivationTokenGenerator.check_token(user, activationToken):
                user_account = UserAccount.objects.get(user=user)
                user_account.email_verified = True
                user_account.save()
                return render(
                    request,
                    template_name="email_templates/successful_account_activation.html",
                )
            else:
                raise
        except Exception as e:
            return render(
                request, template_name="email_templates/failed_account_activation.html"
            )


class DeactivateAccountView(APIView, GlobalViewFunctions):

    def get(self, request):
        self.deactivateAccount(request)
        return Response(
            {
                "success": True,
                "message": "Account deactivated successfully",
            },
            status=200,
        )

    def deactivateAccount(self, request):
        user_account = request.user.useraccount
        user = request.user
        user.is_active = False
        user.save()
        user_account.save()


class UpdateAccountView(APIView, GlobalViewFunctions):

    def post(self, request):
        try:
            updatedAccount = self.updateAccount(request)
            user_accountSerializer = UserAccountSerializer(updatedAccount, many=False)
            return Response(
                {
                    "success": True,
                    "message": "Account updated successfully",
                    "updated_account": user_accountSerializer.data,
                },
                status=200,
            )
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "message": "Failed to update Account",
                    "error": str(e),
                },
                status=500,
            )

    def updateAccount(self, request):
        receivedPayload = request.data.copy()
        user_account = request.user.useraccount
        for key, value in receivedPayload.items():
            self.validateKey(key, request)
            user_account.__setattr__(key, value)
        user_account.save()
        return user_account

    def validateKey(self, key, request):
        if key == "can_create_merchants" or key == "isMerchant":
            exceptionString = f"You don't have permission to modify {key}"
            self.if_user_is_super_admin(request, exceptionString)

    def notifyAllOfUpdate(self):
        # send emails to relevant parties notifiying them of the deactivation:
        pass


class RequestPasswordReset(APIView, GlobalViewFunctions):

    permission_classes = []

    def get(self, request, *args, **kwargs):
        try:
            user_account = UserAccount.objects.get(user__email=kwargs["email"])
            if user_account.password_change_date.date() == timezone.now().date():
                raise Exception("Password can only be reset once every 24hrs.")
            self.send_password_reset_request_email(user_account, request)
            return Response(
                {
                    "message": "Password reset email sent successfully",
                }
            )
        except Exception as e:
            return Response(
                {
                    "message": "Failed to send password reset email",
                    "error": str(e),
                },
                status=500,
            )


class RequestSubmitPasswordResetForm(APIView, GlobalViewFunctions):

    permission_classes = []

    # not a master at security so I'm not sure if doing a token
    # check twice will make a difference
    # my logic: get() <- are you allowed to access the request the form?
    # post() <- are you allowed to post using this form?

    def get(self, request, **kwargs):
        pk = force_str(urlsafe_base64_decode(kwargs["uidb64"]))
        activationToken = kwargs["resetToken"]
        user = User.objects.get(pk=pk)
        if accountActivationTokenGenerator.check_token(user, activationToken):
            context = {
                "pk": kwargs["uidb64"],
                "resetToken": activationToken,
                "success": True
            }
            return render(request, "password_reset_template/reset_password_form.html", context)
        else:
            context = {
                "pk": "",
                "resetToken": "",
                "success": False
            }
            return render(request, "password_reset_template/reset_password_error.html", context)

    def post(self, request, *args, **kwargs):
        try:
            new_password = request.data["newPassword"]
            pk = force_str(urlsafe_base64_decode(kwargs["uidb64"]))
            activationToken = kwargs["resetToken"]
            user = User.objects.get(pk=pk)
            if user.useraccount.password_change_date.date() == timezone.now().date():
                # TODO: return a proper response of password change after 24 hours
                # for now we will return this normal error response
                context = {"pk": "", "resetToken": "", "error": str(e.args[0])}
                return render( 
                    request, "password_reset_template/reset_password_error.html", context
                )
            if accountActivationTokenGenerator.check_token(user, activationToken):
                password_updated = self._update_user_password(new_password, user)
                if password_updated:
                    self.set_user_password_change_date(user)
                    return render(
                        request, "password_reset_template/reset_password_done.html"
                    )
                raise Exception('Failed to update password')
            else:
                raise Exception('Failed to update password')
        except Exception as e:
            context = {"pk": "", "resetToken": "", "error": str(e.args[0])}
            return render(
                request, "password_reset_template/reset_password_error.html", context
            )

    def _update_user_password(self, newPassword, user: User):
        user.set_password(newPassword)
        user.save()
        return True

    def set_user_password_change_date(self, user):
        try:
            user_account = UserAccount.objects.get(user=user)
            user_account.password_change_date = timezone.now()
            user_account.save()
        except Exception as e:
            return Exception('Failed to set user password change date')


class AccountSettingsView(APIView, GlobalViewFunctions):

    permission_classes = []

    def get(self, request, **kwargs):
        try:
            user_account = request.user.useraccount
            user_account_settings = AccountSetting.objects.get(
                user_account=user_account
            )
            num_of_orders_placed = Order.objects.filter(
                transaction__customer=user_account,
                transaction__status=Transaction.COMPLETED,
                status=Order.PENDING_DELIVERY
            ).count()
            num_of_orders_completed = Order.objects.filter(
                transaction__customer=user_account,
                transaction__status=Transaction.COMPLETED,
                status=Order.DELIVERED
            ).count()
            num_of_orders_cancelled = Order.objects.filter(
                transaction__customer=user_account,
                transaction__status=Transaction.CANCELLED,
                status=Order.CANCELLED
            ).count()
            user_account_settings.num_of_orders_placed = num_of_orders_placed
            user_account_settings.num_of_orders_fulfilled = num_of_orders_completed
            user_account_settings.num_of_orders_cancelled = num_of_orders_cancelled
            user_account_settings.save()

            date_joined = user_account.user.date_joined

            account_settings_serialized = AccountSettingsSerializer(
                user_account_settings, many=False
            )
            return Response(
                {
                    "success": True,
                    "message": "Account settings retrieved successfully!",
                    "account_settings": account_settings_serialized.data,
                    "date_joined": date_joined,
                    "email": user_account.user.email
                }
            )
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": f"Failed to get account settings: {e.args[0]}",
                }
            )
        
    def determine_favourite_store(self):
        pass


class DataRequestView(APIView, GlobalViewFunctions):
    
    def get(self, request):
        try:
            data_request = DataRequest()
            data_request.user_account = request.user.useraccount
            self.prep_and_send_data(request.user)
            return Response({
                "success": True,
                "message": "Data request saved successfully"
            })
        except Exception as e:
            return Response({
                "success": False,
                "message": "Failed to save data request",
                "error": e.args[0]
            })

    def prep_and_send_data(self, user):
        # TODO: get all relevant data from users profile:
        # TODO: send this data to provided user email address:
        pass


class UpdateAddressView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def patch(self, request, *args, **kwargs):
        try:
            user_account = UserAccount.objects.get(user=request.user)
            
            if 'address' not in request.data:
                return Response({
                    "success": False,
                    "message": "Invalid data provided",
                    "errors": {"address": ["Address field is required."]}
                }, status=status.HTTP_400_BAD_REQUEST)

            serializer = AddressUpdateSerializer(
                instance=user_account,
                data=request.data,
                partial=True
            )
            
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "success": True,
                    "message": "Address updated successfully",
                    "data": serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "success": False,
                    "message": "Invalid data provided",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except UserAccount.DoesNotExist:
            return Response({
                "success": False,
                "message": "User account not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "success": False,
                "message": "Failed to update address",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
