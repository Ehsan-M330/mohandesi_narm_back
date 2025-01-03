from django.contrib import admin
from main.models import Cart, Food, Order, User
from main.models import Category
from django.contrib.auth.admin import UserAdmin


# Register the User model again
admin.site.register(Food)
admin.site.register(Category)
admin.site.register(Cart)
admin.site.register(User)
admin.site.register(Order)

# admin.site.register(User, UserAdmin)
# admin.site.register(Product, ProductAdmin)
