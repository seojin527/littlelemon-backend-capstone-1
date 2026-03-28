from rest_framework import generics, status, permissions
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User, Group
from .models import Category, MenuItem, Cart, Order, OrderItem
from .serializers import CategorySerializer, MenuItemSerializer, CartSerializer, OrderSerializer, UserSerializer
from datetime import date

# 1. 메뉴 관리 및 조회
class CategoriesView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class MenuItemsView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all().order_by("id")
    serializer_class = MenuItemSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['title', 'category__title']
    ordering_fields = ['price', 'category']
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

# 2. 매니저 그룹 관리 (Admin 전용)
class ManagerUsersView(generics.ListCreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser()]

    def get_queryset(self):
        manager_group = Group.objects.get(name='Manager')
        return User.objects.filter(groups=manager_group)

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        if username:
            user = get_object_or_404(User, username=username)
            manager_group = Group.objects.get(name='Manager')
            manager_group.user_set.add(user)
            return Response({"message": "User added to Manager group"}, status.HTTP_201_CREATED)
        return Response({"error": "Username required"}, status.HTTP_400_BAD_REQUEST)

class ManagerSingleUserView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAdminUser()]

    def delete(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        manager_group = Group.objects.get(name='Manager')
        manager_group.user_set.remove(user)
        return Response({"message": "User removed from Manager group"}, status.HTTP_200_OK)

# 3. 배달원 그룹 관리 (Manager 전용)
class DeliveryCrewUsersView(generics.ListCreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.groups.filter(name='Manager').exists() or self.request.user.is_superuser:
            crew_group = Group.objects.get(name='Delivery crew')
            return User.objects.filter(groups=crew_group)
        return User.objects.none()

    def post(self, request):
        if not (request.user.groups.filter(name='Manager').exists() or request.user.is_superuser):
            return Response({'error': 'Only managers can assign delivery crew users.'}, status=403)
        username = request.data.get('username')
        user = get_object_or_404(User, username=username)
        crew_group = Group.objects.get(name='Delivery crew')
        crew_group.user_set.add(user)
        return Response({"message": "Added to delivery crew"}, status.HTTP_201_CREATED)

# 4. 장바구니 기능 (Customer 전용)
class CartView(generics.ListCreateAPIView, generics.DestroyAPIView):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        menuitem = self.request.data.get('menuitem')
        item = get_object_or_404(MenuItem, pk=menuitem)
        quantity = int(self.request.data.get('quantity'))
        unit_price = item.price
        price = unit_price * quantity
        serializer.save(user=self.request.user, unit_price=unit_price, price=price)

    def delete(self, request):
        Cart.objects.filter(user=request.user).delete()
        return Response(status=204)

# 5. 주문 기능 (Role별 상이)
class OrderView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='Manager').exists() or user.is_superuser:
            return Order.objects.all()
        elif user.groups.filter(name='Delivery crew').exists():
            return Order.objects.filter(delivery_crew=user)
        return Order.objects.filter(user=user)

    def post(self, request):
        cart_items = Cart.objects.filter(user=request.user)
        if not cart_items.exists():
            return Response({"message":"Cart is empty"}, 400)
        
        total = sum([item.price for item in cart_items])
        order = Order.objects.create(user=request.user, status=False, total=total, date=date.today())
        
        for item in cart_items:
            OrderItem.objects.create(order=order, menuitem=item.menuitem, quantity=item.quantity, unit_price=item.unit_price, price=item.price)
            item.delete()
        
        return Response({"message":"Order placed!"}, 201)

class SingleOrderView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.all()

    def patch(self, request, *args, **kwargs):
        order = self.get_object()
        user = request.user
        # 매니저는 배달원 배정 가능
        if user.groups.filter(name='Manager').exists():
            if 'delivery_crew' in request.data:
                crew = get_object_or_404(User, pk=request.data['delivery_crew'])
                order.delivery_crew = crew
            if 'status' in request.data:
                order.status = request.data['status']
            order.save()
            return Response({"message":"Order updated by Manager"})
        # 배달원은 상태값(배달완료)만 수정 가능
        elif user.groups.filter(name='Delivery crew').exists():
            if 'status' in request.data:
                order.status = request.data['status']
                order.save()
                return Response({"message":"Status updated by Crew"})
        return Response(status=403)