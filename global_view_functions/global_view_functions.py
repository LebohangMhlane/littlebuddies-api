

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

from apps.accounts.tokens import accountActivationTokenGenerator

from apps.merchants.models import Branch, MerchantBusiness
from apps.products.models import Product
from apps.products.serializers.serializers import ProductSerializer

import logging

logger = logging.getLogger(__name__)

# functions shared by all views:

class GlobalViewFunctions():

    exceptionStrings = [
        "You do not have permission to delete a product",
        "You don't have permission to update a merchant",
        "You don't have permission to create merchants"
    ]

    def verifyPayloadIntegrity(self, payload:dict, secret="secret"):
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

    def getBranch(self, branchId) -> Branch:
        branch = Branch.objects.get(id=branchId)
        return branch

    def checkIfUserIsSuperAdmin(self, request):
        if request.user.is_superuser and request.user.useraccount.canCreateMerchants:
            return True
        return False
    
    def checkIfUserIsMerchant(self, request):
        if request.user.useraccount.isMerchant: return True
        return False

    def checkIfUserMatchesMerchant(self, request):
        merchant = MerchantBusiness.objects.get(pk=request.data["merchantPk"])
        if merchant.userAccount == request.user.useraccount: return True
        else: return False

    def checkIfUserMatchesProductMerchant(self, request, productMerchant:MerchantBusiness):
        userAccount = request.user.useraccount
        if userAccount == productMerchant.userAccount: return True
        return False

    def notifyAllOfItemCreation(self, instance):
        pass

    def getProducts(self, branch):
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

    def sendActivationEmail(self, userAccount, request):
        mail_subject = "Littlebuddies Email Activation"
        user = User.objects.get(id=userAccount["user"]["id"])
        message = render_to_string(
            "email_templates/email_account_activation.html",
            {
                "userFirstName": userAccount["user"]["first_name"],
                "domain": f"http://{get_current_site(request).domain}",
                "uidb64": urlsafe_base64_encode(force_bytes(user.pk)),
                "activationToken": accountActivationTokenGenerator.make_token(user=user),
                "protocol": "https" if request.is_secure() else "http"
            }
        )
        plain_message = strip_tags(message)
        email = EmailMultiAlternatives(
            mail_subject, plain_message, to=[userAccount["user"]["email"]]
        )
        email.attach_alternative(message, "text/html")
        if email.send():
            pass
        else:
            raise Exception("Failed to send activation email")