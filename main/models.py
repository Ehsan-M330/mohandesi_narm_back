from enum import Enum
from django.db import models

# from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.forms import ValidationError


class UserRole(models.TextChoices):
    ADMIN = "admin", "Admin"
    EMPLOYEE = "employee", "Employee"
    CUSTOMER = "customer", "Customer"


class User(AbstractUser):
    role = models.CharField(max_length=10, choices=UserRole.choices, default="admin")


class Category(models.Model):
    # parent = models.ForeignKey("self" , related_name="categories" , on_delete=models.SET_NULL , null=True , blank=True , )
    name = models.CharField(max_length=60, unique=True)
    image = models.ImageField(upload_to="food_images/", blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "categories"


class OrderStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"


class Order(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    items = models.ManyToManyField("Food", through="OrderItem")
    order_date = models.DateField(auto_now_add=True)
    address = models.TextField()
    status = models.CharField(
        max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} by {self.customer.username}"  # type: ignore


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
        order = Order.objects.create(customer=self.customer, address=address)
        for cart_item in self.cart_items.all():  # type: ignore
            OrderItem.objects.create(
                order=order, food=cart_item.food, quantity=cart_item.quantity
            )
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
    image = models.ImageField(upload_to="food_images/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
