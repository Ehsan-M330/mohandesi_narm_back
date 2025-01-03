from rest_framework import serializers
from main.models import CartItem, Category, Food, Order, User

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, required=True)
    password = serializers.CharField(write_only=True, required=True)

class RegisterCustomerSerializer(serializers.ModelSerializer):
    # name = serializers.CharField(max_length=100)
    # email = serializers.EmailField()
    # phone = serializers.CharField(max_length=20)
    # address = serializers.CharField(max_length=200)
    class Meta:
        model = User
        fields = ["first_name", "username", "password", "email"]
        extra_kwargs = {
            "first_name": {"required": True},
            "username": {"required": True},
            "password": {"write_only": True, "required": True},
            "email": {"required": True},
        }


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id","username","password"]
        
class GetEmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id","username"]
        
class RegisterEmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "password"]
        extra_kwargs = {
            "username": {"required": True},
            "password": {"required": True},
        }
        
class FoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Food
        fields = "__all__"


class AddToCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ["food", "quantity"]
        extra_kwargs = {
            "food": {"required": True},
            "quantity": {"required": True,"min_value": 1},
        }


class GetAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["address"]


class ShowUserFactorSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = "__all__"


class ShowOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = "__all__"



class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"