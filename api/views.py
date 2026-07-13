from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Sum, Count, Q
from .models import Organization, User, Order, Service
from .serializers import OrganizationSerializer, UserProfileSerializer, OrderSerializer, AdminStatSerializer, ServiceSerializer
from .serializers import RegisterSerializer 
from rest_framework.permissions import AllowAny
from rest_framework import generics
from rest_framework import permissions

# 1. Профиль пользователя (Личный кабинет)
class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

# 2. Заказы и Корзина
class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Пользователь видит только свои заказы
        return Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        # Имитация оплаты (как на макете - оплата 10%)
        order = self.get_object()
        order.is_paid = True
        order.save()
        return Response({'status': 'paid', 'promo_code': order.promo_code})

# 3. Админ-панель (Статистика)
class AdminStatsView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminStatSerializer

    def get_queryset(self):
        from django.db.models import Sum, Count, Q
        stats = Organization.objects.annotate(
            orders_count=Count('services__order', filter=Q(services__order__is_paid=True), distinct=True),
            total_sum=Sum('services__price', filter=Q(services__order__is_paid=True))
        ).values('name', 'orders_count', 'total_sum')
        
        return [
            {
                'org_name': s['name'],
                'orders_count': s['orders_count'] or 0,
                'total_sum': s['total_sum'] or 0
            } for s in stats
        ]

# 4. Организации
class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        # Если не админ, видим только проверенные
        if not self.request.user.is_staff:
            qs = qs.filter(is_verified=True)
        
        # Фильтрация из ТЗ
        city = self.request.query_params.get('city')
        if city: qs = qs.filter(city=city)
        # Аналогично для региона и округа...
        return qs
    
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny] # Регистрация доступна всем
    serializer_class = RegisterSerializer    

# Отдельная вьюха для Корзины
class CartView(generics.ListCreateAPIView, generics.DestroyAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Только неоплаченные заказы текущего пользователя
        return Order.objects.filter(user=self.request.user, is_paid=False)

    def perform_create(self, serializer):
        # При создании автоматически привязываем к текущему юзеру
        serializer.save(user=self.request.user)

# Отдельная вьюха для Промокодов (только чтение)
class PurchasedView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Только оплаченные заказы текущего пользователя
        return Order.objects.filter(user=self.request.user, is_paid=True)    
    
# Проверка: является ли пользователь владельцем организации
class IsOrgOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'org'

# 1. Управление своей организацией (Профиль организации)
class MyOrganizationView(generics.RetrieveUpdateAPIView):
    serializer_class = OrganizationSerializer
    permission_classes = [IsOrgOwner]

    def get_object(self):
        # Возвращаем организацию, которой владеет текущий юзер
        return Organization.objects.filter(owner=self.request.user).first()

# 2. Управление своими услугами (Добавление/Удаление номеров или процедур)
class MyServicesViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceSerializer
    permission_classes = [IsOrgOwner]

    def get_queryset(self):
        # Только услуги организации текущего пользователя
        return Service.objects.filter(organization__owner=self.request.user)

    def perform_create(self, serializer):
        # При создании услуги автоматически привязываем её к организации юзера
        org = Organization.objects.filter(owner=self.request.user).first()
        serializer.save(organization=org)

# 3. Список заказов для организации (кто и что купил у этой фирмы)
class OrgOrdersView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsOrgOwner]

    def get_queryset(self):
         return Order.objects.filter(
            services__organization__owner=self.request.user, 
            is_paid=True
        ).distinct()
