from django.contrib import admin
from main.models import Cart, CartItem, Food, Order, OrderItem, User, Category, UserRole
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1  # تعداد فرم‌های خالی برای اضافه کردن آیتم‌ها به کارت
    fields = ('food', 'quantity', 'total_amount')  # فیلدهای نمایشی برای هر آیتم
    readonly_fields = ('total_amount',)  # نمایش فقط خواندنی برای مقدار کل


class CartAdmin(admin.ModelAdmin):
    list_display = ('customer', 'created_at', 'updated_at')
    search_fields = ('customer__username',)
    list_filter = ('customer',)
    ordering = ('-created_at',)
    inlines = [CartItemInline]

    # محدود کردن فیلد customer به فقط کاربران با نقش CUSTOMER
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "customer":
            kwargs["queryset"] = User.objects.filter(role=UserRole.CUSTOMER)  # فقط کاربران با نقش CUSTOMER
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class FoodAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'rate', 'created_at', 'modified_at', 'image_preview')
    search_fields = ('name',)
    list_filter = ('category', 'rate')
    ordering = ('-created_at',)
    list_per_page = 20

    # نمایش تصویر غذا
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Image'  # type: ignore


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    list_per_page = 20


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1  # تعداد فرم‌های خالی برای افزودن آیتم‌ها


class OrderAdmin(admin.ModelAdmin):
    list_display = ('customer', 'status', 'order_date', 'created_at', 'updated_at')
    search_fields = ('customer__username',)
    list_filter = ('status', 'order_date')
    ordering = ('-created_at',)
    inlines = [OrderItemInline]

    # محدود کردن فیلد customer به فقط کاربران با نقش CUSTOMER
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "customer":
            kwargs["queryset"] = User.objects.filter(role=UserRole.CUSTOMER)  # فقط نمایش کاربران با نقش CUSTOMER
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class CartItemAdmin(admin.ModelAdmin):
    list_display = ('food', 'quantity', 'total_amount', 'cart', 'cart_customer')
    list_filter = ('cart', 'food')
    search_fields = ('food__name',)

    def cart_customer(self, obj):
        return obj.cart.customer.username  # نام کاربر را از کارت می‌گیریم
    cart_customer.short_description = 'Customer'  # type: ignore

    list_per_page = 20


admin.site.register(CartItem, CartItemAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)
admin.site.register(Food, FoodAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(User)