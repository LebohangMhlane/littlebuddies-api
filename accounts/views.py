from rest_framework.views import APIView
from rest_framework.response import Response

from accounts.serializers.user_serializer import UserSerializer
# Create your views here.


class CreateAccountView(APIView):

    permission_classes = []

    def get(self, request, *args, **kwargs):
        pass

    def post(self, request, *args, **kwargs):
        self.create_account(post_data=request.data)
        return Response({
            "success": True,
            "account_created": True,
        })

    def create_account(self, post_data=dict):
        user_serializer = UserSerializer(data=post_data)
        if user_serializer.is_valid():
            user_serializer.create(validated_data=post_data)
