from django.contrib.auth.hashers import check_password
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from api.serializers import (
    CategorySerializer,
    DiscountCodeSerializer,
    EmployeeSerializer,
    FoodSerializer,
    GetAddressSerializer,
    GetEmployeeSerializer,
    LoginSerializer,
    RegisterEmployeeSerializer,
)
from api.serializers import AddressSerializer
from api.serializers import RegisterCustomerSerializer
from api.serializers import AddToCartSerializer
from api.serializers import ShowOrderSerializer
from api.serializers import ShowUserCartSerializer
from main.models import Address, Cart, CartItem, Category, DiscountCode, OrderStatus, User
from main.models import Food
from main.models import Order
from main.models import UserRole
from django.contrib.auth import authenticate
from django.core.paginator import Paginator
from datetime import datetime, timedelta

class LogoutAPIView(APIView):
    def post(self, request):
        request.user.auth_token.delete()
        return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)


class LoginAPIView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = request.data.get("username")
            password = request.data.get("password")
            try:
                user = authenticate(username=username, password=password)
                if user is not None:
                    token, created = Token.objects.get_or_create(user=user)
                    return Response({"role": user.role, "token": token.key}, status=status.HTTP_200_OK)  # type: ignore
                else:
                    return Response(
                        {"message": "Invalid credentials"},
                        status=status.HTTP_401_UNAUTHORIZED,
                    )
            except User.DoesNotExist:
                return Response(
                    {"message": "Invalid credentials"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShowFoodsListAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        category = self.request.GET.get("category")
        if category:
            foods = Food.objects.filter(category__name=category).order_by("rate")
        else:
            foods = Food.objects.all()

        paginator = Paginator(foods, 10)
        page_number = request.GET.get("page", 1)
        page = paginator.get_page(page_number)

        #TODO change rate in serializer and handle seled food show in front
        serializer = FoodSerializer(page.object_list, many=True)

        return Response(
            {
                "data": serializer.data,
                "page": page.number,
                "total_pages": paginator.num_pages,
                "total_items": paginator.count,
            },
            status=status.HTTP_200_OK,
        )


class FoodDetailAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request, id):
        try:
            food = Food.objects.get(id=id)
            #TODO check
            serializer = FoodSerializer(food)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Food.DoesNotExist:
            return Response(
                {"message": "Food not found"}, status=status.HTTP_404_NOT_FOUND
            )


# customer
class RgisterCustomerAPIView(APIView):
    def post(self, request):
        serializer = RegisterCustomerSerializer(data=request.data)
        if serializer.is_valid():
            user = User(
                email=serializer.validated_data["email"],  # type: ignore
                username=serializer.validated_data["username"],  # type: ignore
                first_name=serializer.validated_data["first_name"],  # type: ignore
                role=UserRole.CUSTOMER,
            )
            user.set_password(serializer.validated_data["password"])  # type: ignore
            user.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddToCartAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request):
        if request.user.role != UserRole.CUSTOMER:
            return Response(
                {"message": "You are not allowed to add to cart"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Serialize the data
        serializer = AddToCartSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        food_id = serializer.validated_data["food"]  # type: ignore
        quantity = serializer.validated_data["quantity"]  # type: ignore

        try:
            food = Food.objects.get(id=food_id.id)

            cart, created = Cart.objects.get_or_create(customer=request.user)
            cart_item, created = CartItem.objects.get_or_create(cart=cart, food=food)

            if not created:
                cart_item.quantity += quantity
                cart_item.save()
            else:
                cart_item.quantity = quantity
                cart_item.save()
            #TODO no need for rate anymore
            food.rate += 1
            food.save()
            return Response(
                {"message": "Food added to cart"}, status=status.HTTP_200_OK
            )
        except Food.DoesNotExist:
            return Response(
                {"message": "Food not found"}, status=status.HTTP_404_NOT_FOUND
            )


class DeleteFromCartAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def delete(self, request, id):
        if request.user.role != UserRole.CUSTOMER:
            return Response(
                {"message": "You are not allowed to delete from cart"},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            cart_item = CartItem.objects.get(id=id, cart__customer=request.user)
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
                return Response(
                    {
                        "message": "One item removed from cart",
                        "quantity": cart_item.quantity,
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                cart_item.delete()
                return Response(
                    {"message": "Food removed from cart"}, status=status.HTTP_200_OK
                )
        except CartItem.DoesNotExist:
            return Response(
                {"message": "Food not found in cart"}, status=status.HTTP_404_NOT_FOUND
            )


class ShowCartAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        if request.user.role != UserRole.CUSTOMER:
            return Response(
                {"message": "You are not allowed to see cart"},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            cart = Cart.objects.get(customer=request.user)
            cart_items = cart.cart_items.all()  # type: ignore
            if cart_items.exists():
                data = {
                    "cart_items": ShowUserCartSerializer(cart_items, many=True).data,
                    "total_price": sum(item.total_amount() for item in cart_items),
                }
                return Response(data, status=status.HTTP_200_OK)
            else:
                # No items in the cart
                return Response(
                    {"error": "Your cart is empty"}, status=status.HTTP_400_BAD_REQUEST
                )
        except Cart.DoesNotExist:
            return Response(
                {"error": "Cart does not exist"}, status=status.HTTP_404_NOT_FOUND
            )


class CreateOrderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != UserRole.CUSTOMER:
            return Response(
                {"message": "Only customers can create orders."},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        serializer = GetAddressSerializer(data=request.data)
        if serializer.is_valid():
            address_text = serializer.validated_data["address"]  # type: ignore

            try:
                # پیدا کردن یا ایجاد نمونه Address برای کاربر
                address, created = Address.objects.get_or_create(
                    user=request.user, address=address_text
                )

                # دریافت سبد خرید کاربر
                cart = Cart.objects.get(customer=request.user)

                # اطمینان از اینکه سبد خرید خالی نیست
                if not cart.items.exists():
                    return Response(
                        {"error": "Your cart is empty"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # تبدیل سبد خرید به سفارش
                order = cart.convert_to_order(address)

                # پاسخ موفقیت
                return Response(
                    {
                        "message": "Order created successfully",
                        "order_id": order.id,  # type: ignore
                    },
                    status=status.HTTP_201_CREATED,
                )
            except Cart.DoesNotExist:
                return Response(
                    {"error": "Cart not found"}, status=status.HTTP_404_NOT_FOUND
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShowOrderAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        if request.user.role != UserRole.CUSTOMER:
            return Response(
                {"message": "You are not allowed to see orders"},
                status=status.HTTP_403_FORBIDDEN,
            )

        orders = Order.objects.filter(customer=request.user).order_by("-updated_at")

        if not orders.exists():
            return Response(
                {"message": "No orders found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Pagination
        paginator = Paginator(orders, 10)  # 10 orders per page
        page_number = request.GET.get("page", 1)  # Get the page number from the URL
        page = paginator.get_page(page_number)  # Get the current page

        # Serialize the orders
        serializer = ShowOrderSerializer(page.object_list, many=True)
        #TODO check for returning the raeted or not status and be able to cancel if not completed for 30 min
        return Response(
            {
                "data": serializer.data,
                "page": page.number,
                "total_pages": paginator.num_pages,
                "total_items": paginator.count,
            },
            status=status.HTTP_200_OK,
        )


# employee


class ShowPendingOrdersAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        if request.user.role == UserRole.EMPLOYEE:
            orders = Order.objects.filter(status=OrderStatus.PENDING).order_by(
                "-updated_at"
            )

            # Pagination
            paginator = Paginator(orders, 10)  # 10 orders per page
            page_number = request.GET.get("page", 1)  # Get the page number from the URL
            page = paginator.get_page(page_number)  # Get the current page

            # Serialize the orders
            serializer = ShowOrderSerializer(page.object_list, many=True)

            return Response(
                {
                    "data": serializer.data,
                    "page": page.number,
                    "total_pages": paginator.num_pages,
                    "total_items": paginator.count,
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"message": "You are not authorized to access this page"},
                status=status.HTTP_403_FORBIDDEN,
            )


class AcceptAnOrderAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request, id):
        if request.user.role == UserRole.EMPLOYEE:
            try:
                order = Order.objects.get(id=id)
                if order.status != OrderStatus.PENDING:
                    return Response(
                        {"error": "Order is not pending"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                order.status = OrderStatus.ACCEPTED
                order.save()
                return Response(
                    {"message": "Order Accepted successfully"},
                    status=status.HTTP_200_OK,
                )
            except Order.DoesNotExist:
                return Response(
                    {"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND
                )
        else:
            return Response(
                {"message": "You are not authorized to access this page"},
                status=status.HTTP_403_FORBIDDEN,
            )


class ShowAcceptedOrdersAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        if request.user.role == UserRole.EMPLOYEE:
            orders = Order.objects.filter(status=OrderStatus.ACCEPTED).order_by(
                "-updated_at"
            )

            # Pagination
            paginator = Paginator(orders, 10)  # 10 orders per page
            page_number = request.GET.get("page", 1)  # Get the page number from the URL
            page = paginator.get_page(page_number)  # Get the current page

            # Serialize the orders
            serializer = ShowOrderSerializer(page.object_list, many=True)

            return Response(
                {
                    "data": serializer.data,
                    "page": page.number,
                    "total_pages": paginator.num_pages,
                    "total_items": paginator.count,
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"message": "You are not authorized to access this page"},
                status=status.HTTP_403_FORBIDDEN,
            )


# admin


class AddFoodAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request):
        if request.user.role == UserRole.ADMIN:
            serializer = FoodSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                {"message": "You are not authorized to access this page"},
                status=status.HTTP_403_FORBIDDEN,
            )


class DeleteFoodAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def delete(self, request, id):
        if request.user.role == UserRole.ADMIN:
            try:
                food = Food.objects.get(id=id)
                food.delete()
                return Response(
                    {"message": "Food deleted successfully"},
                    status=status.HTTP_204_NO_CONTENT,
                )
            except Food.DoesNotExist:
                return Response(
                    {"error": "Food not found"}, status=status.HTTP_404_NOT_FOUND
                )
        else:
            return Response(
                {"message": "You are not authorized to access this page"},
                status=status.HTTP_403_FORBIDDEN,
            )


class UpdateFoodAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def put(self, request, id):
        if request.user.role == UserRole.ADMIN:
            food = get_object_or_404(Food, id=id)
            serializer = FoodSerializer(food, data=request.data)

            if serializer.is_valid():  # بررسی اعتبار داده‌ها
                serializer.save()  # ذخیره تغییرات
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                {"message": "You are not authorized to access this page"},
                status=status.HTTP_403_FORBIDDEN,
            )


class EmployeesAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    # show employees
    def get(self, request):
        if request.user.role == UserRole.ADMIN:
            employees = User.objects.filter(role=UserRole.EMPLOYEE)
            serializer = GetEmployeeSerializer(employees, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(
                {"message": "You are not authorized to access this page"},
                status=status.HTTP_403_FORBIDDEN,
            )

    # create an employee
    def post(self, request):
        if request.user.role == UserRole.ADMIN:
            serializer = RegisterEmployeeSerializer(data=request.data)
            if serializer.is_valid():
                if User.objects.filter(username=serializer.validated_data["username"]).exists():  # type: ignore
                    return Response(
                        {"message": "Username already exists"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                else:
                    user = User(
                        username=serializer.validated_data["username"],  # type: ignore
                        role=UserRole.EMPLOYEE,
                    )
                    user.set_password(serializer.validated_data["password"])  # type: ignore # Hash the password
                    user.save()

                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                {"message": "You are not authorized to access this page"},
                status=status.HTTP_403_FORBIDDEN,
            )

    # delete an employee
    def delete(self, request, id):
        if request.user.role == UserRole.ADMIN:
            try:
                employee = User.objects.get(id=id)
                employee.delete()
                return Response(
                    {"message": "Employee deleted successfully"},
                    status=status.HTTP_204_NO_CONTENT,
                )
            except User.DoesNotExist:
                return Response()
        else:
            return Response(
                {"message": "You are not authorized to access this page"},
                status=status.HTTP_403_FORBIDDEN,
            )

    def put(self, request, id):
        if request.user.role == UserRole.ADMIN:
            try:
                employee = User.objects.get(id=id)

            except User.DoesNotExist:
                return Response(
                    {"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND
                )
            if employee.role != UserRole.EMPLOYEE:
                return Response(
                    {"error": "User is not an employee"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = EmployeeSerializer(employee, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                {"message": "You are not authorized to access this page"},
                status=status.HTTP_403_FORBIDDEN,
            )


class GetCategoriesAPIView(APIView):
    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)









#narm

class AddAddressAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != UserRole.CUSTOMER:
            return Response(
                {"message": "You are not authorized to access this page"},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        serializer = AddressSerializer(data=request.data)
        if serializer.is_valid():
            # ذخیره مستقیم داده‌ها با مدل Address
            address = Address.objects.create(
                user=request.user,
                address=serializer.validated_data['address'] # type: ignore
            )
            return Response({"address": address.address}, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GetAddressesAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        if request.user.role != UserRole.CUSTOMER:
            return Response(
                {"message": "You are not authorized to access this page"},
                status=status.HTTP_403_FORBIDDEN,
            )
        addresses = Address.objects.filter(user=request.user)
        serializer = GetAddressSerializer(addresses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class CreateDiscountCodeAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request):
        if request.user.role != UserRole.ADMIN:
            return Response(
                {"message": "You are not authorized to access this page"},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = DiscountCodeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ShowDiscountCodesAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        if request.user.role != UserRole.ADMIN:
            return Response(
                {"message": "You are not authorized to access this page"},
                status=status.HTTP_403_FORBIDDEN,
            )
        discount_codes = DiscountCode.objects.all()
        serializer = DiscountCodeSerializer(discount_codes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
class ShowOrderDetailAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request, id):
        if request.user.role != UserRole.CUSTOMER:
            return Response(
                {"message": "You are not authorized to access this page"},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            order = Order.objects.get(id=id)
            if order.customer != request.user:
                return Response(
                    {"error": "You are not authorized to access this page"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            serializer = ShowOrderSerializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND
            )

class CancelOrderAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def delete(self, request, id):
        if request.user.role != UserRole.CUSTOMER:
            return Response(
                {"message": "You are not authorized to access this page"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            order = Order.objects.get(id=id)

            # بررسی مالکیت سفارش
            if order.customer != request.user:
                return Response(
                    {"error": "You are not authorized to cancel this order"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            # بررسی وضعیت سفارش
            if order.status == OrderStatus.ACCEPTED:
                return Response(
                    {"error": "Order already accepted and cannot be canceled"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif order.status == OrderStatus.CANCELLED:
                return Response(
                    {"error": "Order already canceled"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # بررسی زمان سفارش (آیا بیش از 30 دقیقه گذشته است؟)
            time_difference = datetime.now() - order.created_at
            if time_difference > timedelta(minutes=30):
                return Response(
                    {"error": "Order cannot be canceled after 30 minutes"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # تغییر وضعیت سفارش به CANCELLED
            order.status = OrderStatus.CANCELLED
            order.save()

            return Response({"message": "Order canceled successfully"}, status=status.HTTP_200_OK)

        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND
            )