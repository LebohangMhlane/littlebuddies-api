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
from django.template.loader import render_to_string
from django.utils.html import strip_tags

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
            
            voucher_code = self.generate_voucher_code()
            expires_at = timezone.now() + timedelta(days=30)
            
            voucher = Voucher.objects.create(
                code=voucher_code,
                user=request.user.useraccount,  
                referred_email=friend_email,
                expires_at=expires_at,
                discount_amount=10.00
            )

            subject = 'You\'ve Been Referred!'
            
            context = {
                'referrer_email': request.user.email,
                'friend_email': friend_email,
                'voucher_code': voucher_code,
                'expiry_date': expires_at.strftime('%B %d, %Y'),
                'discount_amount': '10.00',
                'website_url': ''
            }
            
            html_message = render_to_string('email_templates/voucher_email.html', context)
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[friend_email],
                html_message=html_message,
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