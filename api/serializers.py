from rest_framework import serializers
from main.models import Address, CartItem, Category, DiscountCode, Food, Order, User

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=150, 
        required=True,
        error_messages={
            "required": "Username is required.",
            "max_length": "Username must not exceed 150 characters.",
        }
    )
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        min_length=8,
        error_messages={
            "required": "Password is required.",
            "min_length": "Password must be at least 8 characters long.",
        }
    )

class RegisterCustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "username", "password", "email"]
        extra_kwargs = {
            "first_name": {
                "required": True,
                "max_length": 50,
                "error_messages": {
                    "required": "First name is required.",
                    "max_length": "First name must not exceed 50 characters.",
                },
            },
            "username": {
                "required": True,
                "max_length": 150,
                "error_messages": {
                    "required": "Username is required.",
                    "max_length": "Username must not exceed 150 characters.",
                },
            },
            "password": {
                "write_only": True,
                "required": True,
                "min_length": 8,
                "error_messages": {
                    "required": "Password is required.",
                    "min_length": "Password must be at least 8 characters long.",
                },
            },
            #TODO better email?
            "email": {
                "required": True,
                "max_length": 254,
                "error_messages": {
                    "required": "Email is required.",
                    "max_length": "Email must not exceed 254 characters.",
                },
            },
        }

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "password"]
        extra_kwargs = {
            "username": {
                "required": True,
                "max_length": 150,
                "error_messages": {
                    "required": "Username is required.",
                    "max_length": "Username must not exceed 150 characters.",
                },
            },
            "password": {
                "write_only": True,
                "required": True,
                "min_length": 8,
                "error_messages": {
                    "required": "Password is required.",
                    "min_length": "Password must be at least 8 characters long.",
                },
            },
        }

class GetEmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]

class RegisterEmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "password"]
        extra_kwargs = {
            "username": {
                "required": True,
                "max_length": 150,
                "error_messages": {
                    "required": "Username is required.",
                    "max_length": "Username must not exceed 150 characters.",
                },
            },
            "password": {
                "required": True,
                "min_length": 8,
                "error_messages": {
                    "required": "Password is required.",
                    "min_length": "Password must be at least 8 characters long.",
                },
            },
        }

class FoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Food
        fields = "__all__"
        extra_kwargs = {
            "name": {
                "required": True,
                "max_length": 100,
                "error_messages": {
                    "required": "Food name is required.",
                    "max_length": "Food name must not exceed 100 characters.",
                },
            },
            "description": {
                "required": True,
                "max_length": 500,
                "error_messages": {
                    "required": "Description is required.",
                    "max_length": "Description must not exceed 500 characters.",
                },
            },
            "price": {
                "required": True,
                "min_value": 0,
                "error_messages": {
                    "required": "Price is required.",
                    "min_value": "Price must be a positive value.",
                },
            },
            "rate": {
                "required": True,
                "min_value": 0,
                "max_value": 100,
                "error_messages": {
                    "required": "Rate is required.",
                    "min_value": "Rate must not be less than 0.",
                    "max_value": "Rate must not exceed 5.",
                },
            },
        }

class AddToCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ["food", "quantity"]
        extra_kwargs = {
            "food": {
                "required": True,
                "error_messages": {
                    "required": "Food is required.",
                },
            },
            "quantity": {
                "required": True,
                "min_value": 1,
                "max_value": 100,
                "error_messages": {
                    "required": "Quantity is required.",
                    "min_value": "Quantity must be at least 1.",
                    "max_value": "Quantity must not exceed 100.",
                },
            },
        }

class AddressSerializer(serializers.Serializer):
    address = serializers.CharField(
        required=True,
        max_length=255,  
        min_length=10,   
        error_messages={
            "required": "Address is required.",
            "max_length": "Address must not exceed 255 characters.",
            "min_length": "Address must be at least 10 characters long."
        }
    )

class GetAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ["address"]
        
class ShowUserCartSerializer(serializers.ModelSerializer):
    food_name = serializers.CharField(source="food.name", read_only=True)
    food_price = serializers.FloatField(source="food.price", read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'food', 'food_name', 'food_price', 'quantity']
        extra_kwargs = {
            "quantity": {
                "min_value": 1,
                "max_value": 100,
                "error_messages": {
                    "min_value": "Quantity must be at least 1.",
                    "max_value": "Quantity must not exceed 100.",
                },
            },
        }

class ShowOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = "__all__"

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"
        extra_kwargs = {
            "name": {
                "required": True,
                "max_length": 50,
                "error_messages": {
                    "required": "Category name is required.",
                    "max_length": "Category name must not exceed 50 characters.",
                },
            },
        }

class DiscountCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscountCode
        fields = "__all__"
        extra_kwargs = {
            "code": {
                "required": True,
                "min_length": 4,
                "max_length": 50,
                "error_messages": {
                    "required": "Discount code is required.",
                    "max_length": "Discount code must not exceed 50 characters.",
                },
            },
            "discount_percent": {
                "required": True,
                "min_value": 0,
                "max_value": 100,
                "error_messages": {
                    "required": "Discount percent is required.",
                    "min_value": "Discount percent must not be less than 0.",
                    "max_value": "Discount percent must not exceed 100.",
                },
            },
        }