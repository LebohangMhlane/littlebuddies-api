
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token


def deleteAllUserRelatedInstances(userPk:int):
    if User.objects.filter(pk=userPk).exists():
        try: Token.objects.get(user__pk=userPk).delete()
        except: pass
        try: User.objects.get(pk=userPk).delete()
        except: pass
        