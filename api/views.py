import json
from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum, Count, Q, F, DecimalField
from django.utils import timezone
from .models import Organization, User, Order, OrderItem, Service, OrganizationSubmission
from .serializers import (
    OrganizationSerializer, UserProfileSerializer, OrderSerializer, 
    OrderItemSerializer, OrganizationSubmissionSerializer, AdminStatSerializer,
    RegisterSerializer  
)

# --- ПЕРМИШЕНЫ ---

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.is_staff

class IsOrgOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'org'

# --- КАТАЛОГ И ПРОФИЛЬ ---

class OrganizationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = OrganizationSerializer
    
    def get_queryset(self):
        queryset = Organization.objects.filter(is_verified=True)
        # Фильтрация по параметрам из CatalogView.vue
        city = self.request.query_params.get('city')
        org_type = self.request.query_params.get('org_type')
        region = self.request.query_params.get('region')
        district = self.request.query_params.get('federal_district')

        if city: queryset = queryset.filter(city=city)
        if org_type: queryset = queryset.filter(org_type=org_type)
        if region: queryset = queryset.filter(region=region)
        if district: queryset = queryset.filter(federal_district=district)
        return queryset

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_object(self):
        return self.request.user

class RegisterView(generics.CreateAPIView): # Возвращено на место
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

# --- КОРЗИНА (CART) ---

class CartView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        cart, created = Order.objects.get_or_create(user=self.request.user, is_paid=False)
        return cart

class CartItemAddView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        service_id = request.data.get('service')
        qty = int(request.data.get('qty', 1))
        cart, _ = Order.objects.get_or_create(user=request.user, is_paid=False)

        if cart.items.count() >= 5 and not cart.items.filter(service_id=service_id).exists():
            return Response({"error": "В корзине не может быть более 5 различных услуг"}, status=400)
        
        item, created = OrderItem.objects.get_or_create(order=cart, service_id=service_id)
        if not created:
            item.qty += qty
        else:
            item.qty = qty
        item.save()
        return Response(OrderSerializer(cart).data, status=status.HTTP_201_CREATED)

class CartItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return OrderItem.objects.filter(order__user=self.request.user, order__is_paid=False)

class CartPayView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        cart = Order.objects.filter(user=request.user, is_paid=False).first()
        if not cart or not cart.items.exists():
            return Response({"error": "Корзина пуста"}, status=400)
        
        cart.is_paid = True
        cart.save() 
        return Response(OrderSerializer(cart).data)

class PurchasedView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user, is_paid=True).order_by('-created_at')

# --- КАБИНЕТ ОРГАНИЗАЦИИ И МОДЕРАЦИЯ ---

class MyOrganizationView(generics.RetrieveAPIView):
    serializer_class = OrganizationSerializer
    permission_classes = [IsOrgOwner]
    def get_object(self):
        return Organization.objects.filter(owner=self.request.user).first()

class SubmitOrganizationView(APIView):
    permission_classes = [IsOrgOwner]

    def post(self, request):
        data = request.data.dict() 
        org_data = json.loads(data.get('org_data', '{}'))
        services_payload = json.loads(data.get('services_payload', '[]'))
        
        submission = OrganizationSubmission.objects.create(
            submitted_by=request.user,
            name=data.get('name'),
            org_type=data.get('org_type'),
            org_data=org_data,
            services_payload=services_payload
        )
        return Response(OrganizationSubmissionSerializer(submission).data, status=201)

class MySubmissionView(generics.RetrieveAPIView):
    serializer_class = OrganizationSubmissionSerializer
    permission_classes = [IsOrgOwner]
    def get_object(self):
        return OrganizationSubmission.objects.filter(submitted_by=self.request.user).order_by('-created_at').first()

# --- АДМИН (МОДЕРАЦИЯ И СТАТИСТИКА) ---

class PendingSubmissionsView(generics.ListAPIView):
    queryset = OrganizationSubmission.objects.filter(status='pending')
    serializer_class = OrganizationSubmissionSerializer
    permission_classes = [permissions.IsAdminUser]

class ApproveSubmissionView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        sub = OrganizationSubmission.objects.get(pk=pk, status='pending')
        org, _ = Organization.objects.update_or_create(
            owner=sub.submitted_by,
            defaults={
                'name': sub.name,
                'org_type': sub.org_type,
                'description': sub.org_data.get('description', ''),
                'federal_district': sub.org_data.get('federal_district', ''),
                'region': sub.org_data.get('region', ''),
                'city': sub.org_data.get('city', ''),
                'address': sub.org_data.get('address', ''),
                'phone': sub.org_data.get('phone', ''),
                'is_verified': True
            }
        )
        org.services.all().delete()
        for s_data in sub.services_payload:
            Service.objects.create(organization=org, **s_data)
        
        sub.status = 'approved'
        sub.reviewed_at = timezone.now()
        sub.save()
        return Response({"status": "approved"})

class RejectSubmissionView(APIView):
    permission_classes = [permissions.IsAdminUser]
    def post(self, request, pk):
        sub = OrganizationSubmission.objects.get(pk=pk)
        sub.status = 'rejected'
        sub.admin_comment = request.data.get('comment', '')
        sub.reviewed_at = timezone.now()
        sub.save()
        return Response({"status": "rejected"})

class AdminStatsView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = AdminStatSerializer

    def get_queryset(self):
        stats = Organization.objects.annotate(
            orders_count=Count('services__orderitem__order', filter=Q(services__orderitem__order__is_paid=True), distinct=True),
            total_sum=Sum(F('services__orderitem__service__price') * F('services__orderitem__qty'), 
                          filter=Q(services__orderitem__order__is_paid=True), output_field=DecimalField())
        ).values('name', 'orders_count', 'total_sum')
        return [{'org_name': s['name'], 'orders_count': s['orders_count'] or 0, 'total_sum': s['total_sum'] or 0} for s in stats]

class OrgOrdersView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsOrgOwner]
    def get_queryset(self):
        return Order.objects.filter(items__service__organization__owner=self.request.user, is_paid=True).distinct()
