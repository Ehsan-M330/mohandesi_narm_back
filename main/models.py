from decimal import Decimal
from enum import Enum
from django.db import models

# from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.forms import ValidationError
from django.utils.timezone import now

class UserRole(models.TextChoices):
    ADMIN = "admin", "Admin"
    EMPLOYEE = "employee", "Employee"
    CUSTOMER = "customer", "Customer"


class User(AbstractUser):
    role = models.CharField(max_length=10, choices=UserRole.choices, default="admin")


class Category(models.Model):
    name = models.CharField(max_length=60, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "categories"


class OrderStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    CANCELLED = "cancelled", "Cancelled"

class Order(models.Model):
    customer = models.ForeignKey(User, on_delete=models.PROTECT, related_name="orders")
    items = models.ManyToManyField("Food", through="OrderItem")
    order_date = models.DateField(auto_now_add=True)
    address = models.ForeignKey("Address", on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")
    status = models.CharField(
        max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    discount_code = models.ForeignKey(
        "DiscountCode", on_delete=models.SET_NULL, null=True, blank=True, related_name="orders"
    )
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    def apply_discount(self):
        if not self.discount_code:
            return self.total_price

        # اعمال درصد تخفیف
        return self.total_price * (1 - self.discount_code.discount_percent / 100)

    def save(self, *args, **kwargs):
        if self.pk:  # مطمئن می‌شویم نمونه ذخیره شده است
            self.total_price = sum(
                item.total_amount() for item in self.order_items.all()  # type: ignore
            )  # محاسبه قیمت کل
            if self.discount_code:
                self.total_price = self.apply_discount()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.id} by {self.customer.username}" # type: ignore



class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="order_items"
    )
    food = models.ForeignKey(
        "Food", on_delete=models.CASCADE, related_name="orderitems"
    )
    quantity = models.IntegerField(default=1)

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError("Quantity must be greater than zero.")

    def total_amount(self):
        return self.quantity * self.food.price

    def __str__(self):
        return f"{self.food.name} (x{self.quantity})"


class Cart(models.Model):
    customer = models.OneToOneField(User, on_delete=models.CASCADE)
    items = models.ManyToManyField("Food", through="CartItem")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def convert_to_order(self, address):
        # ابتدا سفارش را ایجاد می‌کنیم
        order = Order(customer=self.customer, address=address)
        order.save()  # نمونه را ذخیره می‌کنیم تا PK تولید شود
        
        # سپس آیتم‌های سبد خرید را به سفارش اضافه می‌کنیم
        for cart_item in self.cart_items.all():  # type: ignore
            OrderItem.objects.create(
                order=order, food=cart_item.food, quantity=cart_item.quantity
            )
        
        # حذف آیتم‌های سبد خرید
        self.cart_items.all().delete()  # type: ignore

        return order

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="cart_items")
    food = models.ForeignKey("Food", on_delete=models.CASCADE, related_name="cartitems")
    quantity = models.IntegerField(default=1)

    def total_amount(self):
        return self.quantity * self.food.price

    def __str__(self):
        return f"{self.food.name} (x{self.quantity})"


class Food(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="Foods"
    )
    rate = models.IntegerField(default=0)
    #TODO
    image = models.ImageField(upload_to="food_images/", null=True, blank=True,default="food_images/default.jpg")
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    selled=models.IntegerField(default=0)
    def __str__(self):
        return self.name


class DiscountCode(models.Model):
    code = models.CharField(max_length=20, unique=True)
    discount_percent = models.IntegerField(default=0)
    expiration_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def is_valid(self, user):
        # بررسی انقضای کد
        if self.expiration_date < now():
            return False, "This discount code has expired."
        
        # بررسی استفاده قبلی توسط کاربر
        if UserDiscountUse.objects.filter(user=user, discount_code=self).exists():
            return False, "You have already used this discount code."

        return True, "Discount code is valid."

    def __str__(self):
        return self.code

    
class UserDiscountUse(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="used_discounts")
    discount_code = models.ForeignKey(DiscountCode, on_delete=models.CASCADE, related_name="user_uses")
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "discount_code")  # جلوگیری از استفاده مجدد
        verbose_name = "User Discount Use"
        verbose_name_plural = "User Discount Uses"

    def __str__(self):
        return f"{self.user.username} used {self.discount_code.code}"

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")  # ارتباط با کاربر
    address=models.TextField()

    def __str__(self):
        return f"{self.address}"

    class Meta:
        verbose_name = "Address"
        verbose_name_plural = "Addresses"