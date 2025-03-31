from rest_framework import serializers

from apps.app_manager.models import AppManager


class AppManagerSerializer(serializers.ModelSerializer):

    class Meta:
        model = AppManager
        fields = "__all__"
        depth = 3
