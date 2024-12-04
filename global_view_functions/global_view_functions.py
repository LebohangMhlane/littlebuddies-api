

import traceback

import hashlib

from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.models import User

from apps.accounts.models import UserAccount
from apps.accounts.tokens import accountActivationTokenGenerator

from apps.merchants.models import Branch, MerchantBusiness
from apps.products.models import Product
from apps.products.serializers.serializers import ProductSerializer

import logging

from littlebuddies import settings

logger = logging.getLogger(__name__)

# functions shared by all views:

class GlobalViewFunctions():

    exceptionStrings = [
        "You do not have permission to delete a product",
        "You don't have permission to update a merchant",
        "You don't have permission to create merchants"
    ]

    def verify_payload_integrity(self, payload:dict, secret="secret"):
        cleanedPayload = payload.copy()
        checksum_to_compare = cleanedPayload["CHECKSUM"]
        del cleanedPayload["CHECKSUM"]
        values_as_string = "".join(list(cleanedPayload.values()))
        values_as_string += secret
        checksum = hashlib.md5(values_as_string.encode('utf-8')).hexdigest()
        cleanedPayload["CHECKSUM"] = checksum_to_compare
        if checksum_to_compare == checksum:
            return (True, cleanedPayload)   
        else:
            return (False, cleanedPayload)

    def get_branch(self, branchId) -> Branch:
        branch = Branch.objects.get(id=branchId)
        return branch

    def if_user_is_super_admin(self, request):
        if request.user.is_superuser and request.user.useraccount.can_create_merchants:
            return True
        return False
    
    def if_user_is_merchant(self, request):
        if request.user.useraccount.is_merchant: return True
        return False

    def if_user_is_owner(self, request):
        merchant = MerchantBusiness.objects.get(pk=request.data["merchantPk"])
        if merchant.user_account == request.user.useraccount: return True
        else: return False

    def check_if_user_matches_product_merchant(self, request, productMerchant:MerchantBusiness):
        user_account = request.user.useraccount
        if user_account == productMerchant.user_account: return True
        return False

    def notify_all_of_item_creation(self, instance):
        pass

    def get_products(self, branch):
        logger.info("Getting updated stores near customer...")
        try:
            products = Product.objects.filter(
                isActive=True,
                branch=branch,
                inStock=True,
            )
            if products:
                serializer = ProductSerializer(products, many=True)
            else:
                raise Exception("No Product was found")
            return serializer.data
        except Exception as e:
            tb = traceback.format_exc()
            raise Exception(f"{tb}")

    def send_activation_email(self, user_account, request):
        mail_subject = "Littlebuddies Email Activation"
        user = User.objects.get(id=user_account["user"]["id"])
        message = render_to_string(
            "email_templates/email_account_activation.html",
            {
                "userFirstName": user_account["user"]["first_name"],
                "domain": f"http://{get_current_site(request).domain}",
                "uidb64": urlsafe_base64_encode(force_bytes(user.pk)),
                "activationToken": accountActivationTokenGenerator.make_token(user=user),
                "protocol": "https" if request.is_secure() else "http"
            }
        )
        plain_message = strip_tags(message)
        email = EmailMultiAlternatives(
            mail_subject, plain_message, to=[user_account["user"]["email"]]
        )
        email.attach_alternative(message, "text/html")
        if settings.DEBUG:
            if email.send():
                pass
            else:
                raise Exception("Failed to send activation email")
        
    def send_password_reset_request_email(self, user_account:UserAccount, request):
        mail_subject = "Littlebuddies Password Reset"
        user = user_account.user
        context = {
            "userFirstName": user.first_name,
            "domain": f"{'https' if request.is_secure() else 'http'}://{get_current_site(request).domain}",
            "uidb64": urlsafe_base64_encode(force_bytes(user.pk)),
            "resetToken": accountActivationTokenGenerator.make_token(user=user),
            "protocol": "https" if request.is_secure() else "http"
        }
        message = render_to_string(
            "email_templates/email_reset_password.html", context
        )
        plain_message = strip_tags(message)
        email = EmailMultiAlternatives(
            mail_subject, plain_message, to=[user.email]
        )
        email.attach_alternative(message, "text/html")
        if email.send():
            return True
        else:
            raise Exception("Failed to password reset request")