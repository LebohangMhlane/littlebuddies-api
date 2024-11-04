from rest_framework import serializers
from .models import Voucher

class ReferralSerializer(serializers.Serializer):
    friend_email = serializers.EmailField()

class VoucherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voucher
        fields = ['code', 'referred_email', 'is_claimed', 'created_at', 'expires_at', 'discount_amount']