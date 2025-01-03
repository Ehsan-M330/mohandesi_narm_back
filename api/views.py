from django.contrib.auth.hashers import check_password
from django.shortcuts import render
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from django.views.decorators.csrf import csrf_exempt
from api.serializers import (
    EmployeeSerializer,
    FoodSerializer,
    RegisterEmployeeSerializer,
)
from api.serializers import GetAddressSerializer
from api.serializers import RegisterCustomerSerializer
from api.serializers import AddToCartSerializer
from api.serializers import ShowOrderSerializer
from api.serializers import ShowUserFactorSerializer
from main.models import CartItem, OrderStatus, User
from main.models import Food
from main.models import Order
from main.models import UserRole
from rest_framework.decorators import permission_classes


# class CustomObtainAuthToken(ObtainAuthToken):
#     @csrf_exempt
#     def post(self, request, *args, **kwargs):
#         # Call the original method to authenticate and get the token
#         response = super().post(request, *args, **kwargs)

#         username = request.data.get("username")
#         password = request.data.get("password")
#         try:
#             user = User.objects.get(username=username)
#             if check_password(password, user.password):
#                 token=Token.objects.get(user=user)
#                 return Response({"role": user.role,"token": token.key})
#             else:
#                 return Response(
#                     {"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
#                 )
#         except User.DoesNotExist:
#             return Response(
#                 {"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
#             )


# # Get user details from the request
# username = request.data.get('username')
# password = request.data.get('password')

# try:
#     user = User.objects.get(username=username)

#     # Verify the password
#     if user.check_password(password):
#         token, created = Token.objects.get_or_create(user=user)
#         if username == "Erfanjz7" and password == "kelase6om":# Fallback to 'guest' if no role is set
#             return Response({
#                 'token': token.key,
#                 'role': "admin"
#             }, status=status.HTTP_200_OK)
#         elif username == "Employee1" and password == "Emp1" or username == "Employee2" and password == "Emp2" or username == "Employee3" and password == "Emp3":
#             return Response({
#                 'token': token.key,
#                 'role': "employee"
#             }, status=status.HTTP_200_OK)
#         elif username != "Erfanjz7":  # If the username is not "Erfanjz7", assign 'customer' role
#             return Response({
#                 'token': token.key,
#                 'role': "customer"
#             }, status=status.HTTP_200_OK)

#     return Response({"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

# except User.DoesNotExist:
#     return Response({"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutAPIView(APIView):
    def post(self, request):
        request.user.auth_token.delete()
        return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)


# TODO
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


# class CustomerDashboardView(APIView):
#     permission_classes = [
#         IsAuthenticated,
#     ]

#     def get(self, request):
#         user = request.user
#         orders = Order.objects.filter(customer=user)
#         serializer = ShowOrderSerializer(orders, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)


class AddToCartAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request):
        # TODO check user
        serializer = AddToCartSerializer(data=request.data)
        food_id = serializer.validated_data["Food"]  # type: ignore
        quantity = serializer.validated_data["quantity"]  # type: ignore
        try:
            food = Food.objects.get(id=food_id)
            # TODO check
            cart_item, created = CartItem.objects.get_or_create(
                customer=request.user, food=food
            )
            # TODO check quantity
            if not created:
                cart_item.quantity += quantity
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


# TODO check
class ShowOrderAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
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

# TODO
# class EmployeeDashboardView(APIView):

#     permission_classes = [
#         IsAuthenticated,
#     ]

#     def get(self, request):
#         user = request.user
#         orders = Order.objects.filter(status='Pending')
#         serializer = ShowOrderSerializer(orders, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)


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

    def post(self, request, order_id):
        if request.user.role == UserRole.EMPLOYEE:
            try:
                order = Order.objects.get(id=order_id)
                if order.status != OrderStatus.PENDING:
                    return Response(
                        {"error": "Order is not pending"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                order.status = OrderStatus.Accepted
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
            orders = Order.objects.filter(status=OrderStatus.Accepted)
            serializer = ShowOrderSerializer(orders, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(
                {"message": "You are not authorized to access this page"},
                status=status.HTTP_403_FORBIDDEN,
            )


# admin
# TODO
# class AdminDashboardView(APIView):
#     permission_classes = [
#         IsAuthenticated,
#     ]

#     def get(self, request):
#         if User.role==UserRole.ADMIN:
#             user = request.user
#             orders = Order.objects.all()
#             serializer = ShowOrderSerializer(orders, many=True)
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         else:
#             return Response({"message": "You are not authorized to access this page"}, status=status.HTTP_401_UNAUTHORIZED)


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


# TODO
class UpdateFoodAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def put(self, request, food_id):
        if request.user.role == UserRole.ADMIN:
            try:
                food = Food.objects.get(id=food_id)
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
            serializer = EmployeeSerializer(employees, many=True)
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
    def delete(self, request, employee_id):
        if request.user.role == UserRole.ADMIN:
            try:
                employee = User.objects.get(id=employee_id)
                employee.delete()
                return Response(
                    {"message": "Employee deleted successfully"},
                    status=status.HTTP_204_NO_CONTENT,
                )
            except User.DoesNotExist:
                return Response(
                    {"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND
                )
        else:
            return Response(
                {"message": "You are not authorized to access this page"},
                status=status.HTTP_403_FORBIDDEN,
            )

    # TODO UPDATE?


# class ShowresturantsAPIView(APIView):
#     # permission_classes = [
#     #     IsAuthenticated,
#     # ]

#     def get(self, request):
#         resturants = Resturant.objects.all()
#         serializer = ResturantSerializer(resturants, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)


# class ShowresturantAPIView(APIView):
#     # permission_classes = [
#     #     IsAuthenticated,
#     # ]

#     def get(self, request , resturant_id):
#         try:
#             resturant = Resturant.objects.get(id=resturant_id)
#             serializer = ResturantSerializer(resturant)  # Don't use many=True for a single instance
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         except Resturant.DoesNotExist:
#             return Response({"detail": "Restaurant not found."}, status=status.HTTP_404_NOT_FOUND)


# class ResturantDetailAPIView(APIView):
#     # parser_classes = [
#     #     IsAuthenticated,
#     # ]

#     def get(self, request, resturant_id):
#         try:
#             # Retrieve the restaurant by its ID
#             resturant = Resturant.objects.get(id=resturant_id)

#             # Retrieve all foods related to this restaurant
#             foods = resturant.food.all()

#             # Serialize the food data
#             food_data = FoodSerializer(foods, many=True)

#             # Return the list of foods
#             return Response(food_data.data, status=status.HTTP_200_OK)

#         except Resturant.DoesNotExist:
#             return Response({"detail": "Restaurant not found."}, status=status.HTTP_404_NOT_FOUND)


# class ShowFoodAPIView(APIView):
#     # permission_classes = [
#     #     IsAuthenticated,
#     # ]

#     def get(self, request , food_id , resturant_id):
#         resturant = Resturant.objects.get(id=resturant_id)
#         foods = resturant.food.get(id=food_id)
#         serializer = FoodSerializer(foods)
#         return Response(serializer.data, status=status.HTTP_200_OK)
