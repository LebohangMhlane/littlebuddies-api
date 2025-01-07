
from apps.products.models import BranchProduct, Product
import custom_admin_site


custom_admin_site.custom_admin_site.register(Product)
custom_admin_site.custom_admin_site.register(BranchProduct)
