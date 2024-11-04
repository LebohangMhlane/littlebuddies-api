from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import random
import string
from datetime import timedelta

from .serializers import ReferralSerializer
from .models import Voucher

class ReferralView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def generate_voucher_code(self):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    def post(self, request):
        serializer = ReferralSerializer(data=request.data)
        if serializer.is_valid():
            friend_email = serializer.validated_data['friend_email']
            
            # Generate voucher
            voucher_code = self.generate_voucher_code()
            expires_at = timezone.now() + timedelta(days=30)
            
            # Create voucher
            voucher = Voucher.objects.create(
                code=voucher_code,
                user=request.user.useraccount,  
                referred_email=friend_email,
                expires_at=expires_at,
                discount_amount=10.00
            )

            # Send email, i need to create a template
            subject = 'You\'ve Been Referred!'
            message = f'''
            Hello!

            Your friend {request.user.email} has referred you!
            Here's your voucher code: {voucher_code}

            This voucher is valid for 30 days.
            '''
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [friend_email],
                fail_silently=False,
            )

            return Response({
                'success': True,
                'voucher_code': voucher_code
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class ClaimVoucherView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        voucher_code = request.data.get('voucher_code')
        try:
            voucher = Voucher.objects.get(
                code=voucher_code,
                is_claimed=False,
                expires_at__gt=timezone.now()
            )
            voucher.is_claimed = True
            voucher.save()
            
            return Response({
                'success': True,
                'message': 'Voucher claimed successfully',
                'discount_amount': voucher.discount_amount
            }, status=status.HTTP_200_OK)  
            
        except Voucher.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Invalid or expired voucher code'
            }, status=status.HTTP_400_BAD_REQUEST)