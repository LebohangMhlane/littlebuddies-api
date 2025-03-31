from apps.paystack.models import Payment
from custom_admin_site import custom_admin_site
from django.contrib import admin


class PaymentAdmin(admin.ModelAdmin):

    list_display = ["email", "amount", "reference", "paid", "created_at"]

    list_filter = ()

    search_fields = ()

    readonly_fields = ()

    exclude = []

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.useraccount.is_super_user:
            return qs
        return []

    def get_readonly_fields(self, request, obj=None):
        if not request.user.useraccount.is_super_user:
            return self.list_display
        return []

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=...):
        return False

    def has_delete_permission(self, request, obj=...):
        return False


custom_admin_site.register(Payment, PaymentAdmin)
