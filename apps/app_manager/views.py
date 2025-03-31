from rest_framework.views import APIView
from rest_framework.response import Response

from apps.app_manager.models import AppManager
from apps.app_manager.serializers import AppManagerSerializer


class AppManagerView(APIView):

    def get(self, request, *args, **kwargs):

        """
        return a app manager instance as a json
        """

        try:
            app_manager = AppManager.objects.all().first()
            app_manager_serialized = AppManagerSerializer(app_manager, many=False)
            return Response({
                "success": True,
                "message": "App manager instance retrieved successfully",
                "data": app_manager_serialized.data}, status=200)
        except AppManager.DoesNotExist:
            return Response({
                "success": False,
                "message": "App manager instance not found"}, status=404)
