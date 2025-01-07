
from apps.transactions.models import Transaction
import custom_admin_site

custom_admin_site.custom_admin_site.register(Transaction)
