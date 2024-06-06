from django.contrib import admin

from apps.products.models import BranchProduct, Product


admin.site.register(Product)
admin.site.register(BranchProduct)
