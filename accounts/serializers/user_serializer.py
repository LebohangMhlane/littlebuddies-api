
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from global_serializer_functions.global_serializer_functions import deleteAllUserRelatedInstances


class UserSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = "__all__"

    def is_valid(self, *, raise_exception=False):
        initialData = self.initial_data
        if(
            self.emailIsValid(initialData["email"]), 
            self.usernameIsValid(initialData["username"])):
            return True
        else:
            raise Exception("Invalid User Data")
            
    def emailIsValid(self, email):
        # TODO: implement email validation:
        pass

    def usernameIsValid(self, username):
        # TODO: implement username validation:
        pass

    def create(self, validated_data):
        user = User()
        user.username = validated_data["username"]
        user.password = make_password(validated_data["password"]) 
        user.email = validated_data["email"]
        user.first_name = validated_data["firstName"]
        user.last_name = validated_data["lastName"]
        user.save()
        self.createUserAuthenticationToken(user)
        return user
    
    def createUserAuthenticationToken(self, user):
        try:
            Token.objects.create(user=user)
        except:
            deleteAllUserRelatedInstances()
            raise Exception("Failed to create user token")