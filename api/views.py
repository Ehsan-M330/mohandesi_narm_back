from django.contrib.auth.hashers import check_password
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from api.serializers import (
    EmployeeSerializer,
    FoodSerializer,
    GetEmployeeSerializer,
    RegisterEmployeeSerializer,
)
from api.serializers import GetAddressSerializer
from api.serializers import RegisterCustomerSerializer
from api.serializers import AddToCartSerializer
from api.serializers import ShowOrderSerializer
from api.serializers import ShowUserFactorSerializer
from main.models import Cart, CartItem, OrderStatus, User
from main.models import Food
from main.models import Order
from main.models import UserRole


class LogoutAPIView(APIView):
    def post(self, request):
        request.user.auth_token.delete()
        return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)


class LoginAPIView(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        try:
            user = User.objects.get(username=username)
            if check_password(password, user.password):
                token, created = Token.objects.get_or_create(user=user)
                return Response({"role": user.role, "token": token.key})
            else:
                return Response(
                    {"message": "Invalid credentials"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
        except User.DoesNotExist:
            return Response(
                {"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )


class ShowFoodsListAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    # TODO pagination
    def get(self, request):
        category = self.request.GET.get("category")
        if category:
            foods = Food.objects.filter(category__name=category).order_by("rate")
        else:
            foods = Food.objects.all()
        serializer = FoodSerializer(foods, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class FoodDetailAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request, id):
        try:
            food = Food.objects.get(id=id)
            serializer = FoodSerializer(food)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Food.DoesNotExist:
            return Response(
                {"message": "Food not found"}, status=status.HTTP_404_NOT_FOUND
            )


# customer
# TODO username
class RgisterCustomerAPIView(APIView):
    def post(self, request):
        serializer = RegisterCustomerSerializer(data=request.data)
        if serializer.is_valid():
            # if User.objects.filter(username=serializer.validated_data["username"]):  # type: ignore
            #     return Response(
            #         {"message": "Username already exists"},
            #         status=status.HTTP_400_BAD_REQUEST,
            #     )

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


# TODO ?
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
        serializer = AddToCartSerializer(data=request.data)
        food_id = serializer.validated_data["Food"]  # type: ignore
        quantity = serializer.validated_data["quantity"]  # type: ignore
        try:
            food = Food.objects.get(id=food_id)
            cart_item, created = CartItem.objects.get_or_create(
                customer=request.user, food=food
            )
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
            else:
                cart_item.quantity = quantity
                cart_item.save()
            return Response(
                {"message": "Food added to cart"}, status=status.HTTP_200_OK
            )
        except Food.DoesNotExist:
            return Response(
                {"message": "Food not found"}, status=status.HTTP_404_NOT_FOUND
            )


# TODO check
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
            cart_items = cart.cart_items.all()  # type: ignore # Access related CartItem objects
            if cart_items.exists():
                data = {
                    "cart_items": ShowUserFactorSerializer(cart_items, many=True).data,
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


# TODO check
class ShowOrderAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]
    # TODO pagination

    def get(self, request):
        if request.user.role != UserRole.CUSTOMER:
            return Response(
                {"message": "You are not allowed to see orders"},
                status=status.HTTP_403_FORBIDDEN,
            )
        orders = Order.objects.filter(customer=request.user)
        serializer = ShowOrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ShowUserFactorAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request):
        serializer = GetAddressSerializer(data=request.data)
        if serializer.is_valid():
            address = serializer.validated_data["address"]  # type: ignore

            # Get cart items and associate the `Food` objects with the order
            cart_items = CartItem.objects.filter(customer=request.user)
            if cart_items.exists():
                data = {
                    "cart_items": ShowUserFactorSerializer(cart_items, many=True).data,
                    "total_price": sum(item.total_amount() for item in cart_items),
                }
                return Response(data, status=status.HTTP_201_CREATED)
            else:
                # No items in the cart
                return Response(
                    {"error": "Your cart is empty"}, status=status.HTTP_400_BAD_REQUEST
                )

        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateOrderAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request):
        serializer = GetAddressSerializer(data=request.data)
        if serializer.is_valid():
            address = serializer.validated_data["address"]  # type: ignore

            # Create the order
            order = Order.objects.create(customer=request.user, address=address)

            # Get cart items and associate the `Food` objects with the order
            cart_items = CartItem.objects.filter(customer=request.user)
            if cart_items.exists():
                foods = [
                    item.food for item in cart_items  # type: ignore
                ]  # Assuming `CartItem` has a `food` ForeignKey
                order.items.set(foods)  # Link the Food objects to the order

                # Clear the cart
                cart_items.delete()

                return Response(
                    {"message": "Order created successfully"},
                    status=status.HTTP_201_CREATED,
                )
            else:
                # No items in the cart
                return Response(
                    {"error": "Your cart is empty"}, status=status.HTTP_400_BAD_REQUEST
                )

        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# employee


class ShowPendingOrdersAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        if request.user.role == UserRole.EMPLOYEE:
            orders = Order.objects.filter(status=OrderStatus.PENDING)
            serializer = ShowOrderSerializer(orders, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
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
            orders = Order.objects.filter(status=OrderStatus.ACCEPTED)
            serializer = ShowOrderSerializer(orders, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
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
            try:
                food = Food.objects.get(id=id)
                serializer = FoodSerializer(food, data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except Food.DoesNotExist:
                return Response(
                    {"error": "Food not found"}, status=status.HTTP_404_NOT_FOUND
                )
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
                    User.objects.create(
                        username=serializer.validated_data["username"],  # type: ignore
                        password=serializer.validated_data["password"],  # type: ignore
                        role=UserRole.EMPLOYEE,
                    )
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
                return Response(
                )
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
