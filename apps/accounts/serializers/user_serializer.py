
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from global_serializer_functions.global_serializer_functions import SerializerFunctions


class UserSerializer(serializers.ModelSerializer, SerializerFunctions):
    
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "email", "is_superuser", "is_staff", "username"]

    def is_valid(self, *, raise_exception=False):
        initialData = self.initial_data
        if self.validateEmail(initialData["email"]):
            return True
        else:
            raise Exception("Invalid User Data")
            
    def validateEmail(self, email):
        # TODO: implement email validation:
        return True

    def create(self, validated_data):
        try:
            user = User()
            user.username = validated_data["username"]
            user.password = make_password(validated_data["password"]) 
            user.email = validated_data["email"]
            user.first_name = validated_data["firstName"]
            user.last_name = validated_data["lastName"]
            user.save()
            self.createUserAuthenticationToken(user)
            return user
        except Exception as e:
            if user.pk:
                self.deleteAllUserRelatedInstances(userPk=user.pk)
            raise Exception(f"Failed to create User: {str(e.args[0])}")
    
    def createUserAuthenticationToken(self, user):
        try:
            Token.objects.create(user=user)
        except:
            self.deleteAllUserRelatedInstances(userPk=user.pk)
            raise Exception("Failed to create user token")