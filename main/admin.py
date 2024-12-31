from django.contrib import admin
from main.models import Cart, Food, User
from main.models import Category


# Register the User model again
admin.site.register(Food)
admin.site.register(Category)
admin.site.register(Cart)
# admin.site.register(User)

from django.contrib.auth.admin import UserAdmin


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'image']


class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'category', 'price', 'image', 'is_active']


admin.site.register(User, UserAdmin)
# admin.site.register(Product, ProductAdmin)