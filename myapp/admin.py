from django.contrib import admin
from .models import Product, Category, UserProfile, ShippingAddress

# Register your models here.

admin.site.register(Product)
admin.site.register(Category)
admin.site.register(UserProfile)
admin.site.register(ShippingAddress)



