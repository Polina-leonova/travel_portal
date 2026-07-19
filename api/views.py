import json
from django.utils import timezone
from django.db.models import Sum, Count, Q, F, DecimalField, Avg
from rest_framework import viewsets, generics, status, permissions
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny

from .models import Organization, User, Order, OrderItem, Service, OrganizationSubmission, Review
from .serializers import (
    OrganizationSerializer, UserProfileSerializer, OrderSerializer,
    OrderItemSerializer, AdminStatSerializer, ServiceSerializer, RegisterSerializer,
    OrganizationSubmissionSerializer, ReviewSerializer,
)
from django.shortcuts import get_object_or_404


# ---------- Профиль ----------
class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer


# ---------- Организации (каталог + модерация) ----------
class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.is_staff


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_staff:
            qs = qs.filter(is_verified=True)

        org_type = self.request.query_params.get('org_type')
        if org_type:
            qs = qs.filter(org_type=org_type)
        federal_district = self.request.query_params.get('federal_district')
        if federal_district:
            qs = qs.filter(federal_district=federal_district)
        region = self.request.query_params.get('region')
        if region:
            qs = qs.filter(region=region)
        city = self.request.query_params.get('city')
        if city:
            qs = qs.filter(city=city)

        return qs


# ---------- Корзина ----------
class CartView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        order, _ = Order.objects.get_or_create(user=self.request.user, is_paid=False)
        return order


class CartItemAddView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        service_id = request.data.get('service')
        qty = int(request.data.get('qty', 1))
        if not service_id or qty < 1:
            return Response({'detail': 'Некорректные данные'}, status=status.HTTP_400_BAD_REQUEST)

        service = get_object_or_404(Service, pk=service_id)
        order, _ = Order.objects.get_or_create(user=request.user, is_paid=False)

        item, created = OrderItem.objects.get_or_create(
            order=order, service=service, defaults={'qty': qty},
        )
        if not created:
            item.qty += qty
            item.save()

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class CartItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return OrderItem.objects.filter(order__user=self.request.user, order__is_paid=False)


class CartPayView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order = get_object_or_404(Order, user=request.user, is_paid=False)
        if not order.items.exists():
            return Response({'detail': 'Корзина пуста'}, status=status.HTTP_400_BAD_REQUEST)

        order.is_paid = True
        order.save()

        return Response({'status': 'paid', 'promo_code': order.promo_code})


class PurchasedView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user, is_paid=True).order_by('-created_at')


class AdminStatsView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminStatSerializer

    def get_queryset(self):
        stats = Organization.objects.annotate(
            orders_count=Count(
                'services__orderitem__order',
                filter=Q(services__orderitem__order__is_paid=True),
                distinct=True,
            ),
            total_sum=Sum(
                F('services__orderitem__service__price') * F('services__orderitem__qty'),
                filter=Q(services__orderitem__order__is_paid=True),
                output_field=DecimalField(),
            ),
            avg_rating=Avg('reviews__rating', filter=Q(reviews__status='approved')),
        ).values('name', 'orders_count', 'total_sum', 'avg_rating')

        return [
            {
                'org_name': s['name'],
                'orders_count': s['orders_count'] or 0,
                'total_sum': s['total_sum'] or 0,
                'avg_rating': round(s['avg_rating'], 1) if s['avg_rating'] else None,
            }
            for s in stats
        ]


# ---------- Кабинет организации ----------
class IsOrgOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'org'


class MyOrganizationView(generics.GenericAPIView):
    serializer_class = OrganizationSerializer
    permission_classes = [IsOrgOwner]

    def get(self, request):
        org = Organization.objects.filter(owner=request.user).first()
        if not org:
            return Response(None)
        return Response(self.get_serializer(org).data)


class MySubmissionView(generics.GenericAPIView):
    serializer_class = OrganizationSubmissionSerializer
    permission_classes = [IsOrgOwner]

    def get(self, request):
        submission = OrganizationSubmission.objects.filter(
            submitted_by=request.user,
        ).order_by('-created_at').first()
        if not submission:
            return Response(None)
        return Response(self.get_serializer(submission).data)


class SubmitOrganizationView(generics.GenericAPIView):
    serializer_class = OrganizationSubmissionSerializer
    permission_classes = [IsOrgOwner]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        user = request.user

        if OrganizationSubmission.objects.filter(submitted_by=user, status='pending').exists():
            return Response({'detail': 'У вас уже есть заявка на рассмотрении'}, status=status.HTTP_400_BAD_REQUEST)

        data = request.data.dict()  # <-- было request.data.copy()
        for field in ('perks', 'general_amenities', 'services_payload'):
            raw = data.get(field)
            if isinstance(raw, str):
                try:
                    data[field] = json.loads(raw)
                except (TypeError, ValueError):
                    return Response({field: 'Некорректный формат данных'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        existing_org = Organization.objects.filter(owner=user).first()
        serializer.save(submitted_by=user, organization=existing_org)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrgOrdersView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsOrgOwner]

    def get_queryset(self):
        return Order.objects.filter(
            items__service__organization__owner=self.request.user,
            is_paid=True,
        ).distinct()


# ---------- Модерация заявок (админ) ----------
class PendingSubmissionsView(generics.ListAPIView):
    serializer_class = OrganizationSubmissionSerializer
    permission_classes = [IsAdminUser]
    queryset = OrganizationSubmission.objects.filter(status='pending').order_by('created_at')


class ApproveSubmissionView(generics.GenericAPIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        submission = get_object_or_404(OrganizationSubmission, pk=pk, status='pending')

        org = submission.organization or Organization(owner=submission.submitted_by)
        org.org_type = submission.org_type
        org.name = submission.name
        org.description = submission.description
        org.federal_district = submission.federal_district
        org.region = submission.region
        org.city = submission.city
        org.address = submission.address
        org.latitude = submission.latitude
        org.longitude = submission.longitude
        org.phone = submission.phone
        org.working_hours = submission.working_hours
        org.perks = submission.perks
        org.general_amenities = submission.general_amenities
        if submission.image:
            org.image = submission.image
        org.is_verified = True
        org.save()

        # полная замена услуг данными из заявки
        org.services.all().delete()
        for item in submission.services_payload:
            Service.objects.create(
                organization=org,
                category=item.get('category', ''),
                name=item.get('name', ''),
                description=item.get('description', ''),
                price=item.get('price') or 0,
                capacity=item.get('capacity') or None,
                amenities=item.get('amenities') or [],
                date_start=item.get('date_start') or None,
                date_end=item.get('date_end') or None,
                itinerary=item.get('itinerary') or [],
                included=item.get('included') or [],
            )

        submission.organization = org
        submission.status = 'approved'
        submission.reviewed_at = timezone.now()
        submission.save()

        return Response(OrganizationSerializer(org).data)


class RejectSubmissionView(generics.GenericAPIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        submission = get_object_or_404(OrganizationSubmission, pk=pk, status='pending')
        submission.status = 'rejected'
        submission.admin_comment = request.data.get('comment', '')
        submission.reviewed_at = timezone.now()
        submission.save()
        return Response({'status': 'rejected'})


class ReviewListView(generics.ListAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Review.objects.filter(status='approved')
        org_id = self.request.query_params.get('organization')
        if org_id:
            qs = qs.filter(organization_id=org_id)
        return qs


class SubmitReviewView(generics.GenericAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        org_id = request.data.get('organization')
        rating = request.data.get('rating')
        text = request.data.get('text', '')

        if not org_id or not rating:
            return Response({'detail': 'Укажите организацию и оценку'}, status=status.HTTP_400_BAD_REQUEST)

        review, _ = Review.objects.update_or_create(
            organization_id=org_id, user=request.user,
            defaults={'rating': rating, 'text': text, 'status': 'pending', 'reviewed_at': None},
        )
        return Response(self.get_serializer(review).data, status=status.HTTP_201_CREATED)


class MyReviewView(generics.GenericAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org_id = request.query_params.get('organization')
        review = Review.objects.filter(organization_id=org_id, user=request.user).first()
        if not review:
            return Response(None)
        return Response(self.get_serializer(review).data)


# ---------- Модерация отзывов (админ) ----------
class PendingReviewsView(generics.ListAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAdminUser]
    queryset = Review.objects.filter(status='pending').order_by('created_at')


class AllReviewsView(generics.ListAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAdminUser]
    queryset = Review.objects.all().order_by('-created_at')


class ApproveReviewView(generics.GenericAPIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk, status='pending')
        review.status = 'approved'
        review.reviewed_at = timezone.now()
        review.save()
        return Response(ReviewSerializer(review).data)


class RejectReviewView(generics.GenericAPIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk, status='pending')
        review.status = 'rejected'
        review.reviewed_at = timezone.now()
        review.save()
        return Response({'status': 'rejected'})


class AdminReviewDeleteView(generics.DestroyAPIView):
    queryset = Review.objects.all()
    permission_classes = [IsAdminUser]
