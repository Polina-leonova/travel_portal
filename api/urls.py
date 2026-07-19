from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    OrganizationViewSet, UserProfileView, AdminStatsView, RegisterView,
    CartView, CartItemAddView, CartItemDetailView, CartPayView, PurchasedView,
    MyOrganizationView, MySubmissionView, SubmitOrganizationView, OrgOrdersView,
    PendingSubmissionsView, ApproveSubmissionView, RejectSubmissionView
)

# Используем роутер только для публичного каталога организаций
router = DefaultRouter()
router.register(r'organizations', OrganizationViewSet, basename='organization')

urlpatterns = [
    path('', include(router.urls)),

    # 1. Авторизация
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='register'),

    # 2. Личный кабинет пользователя (Профиль)
    path('profile/', UserProfileView.as_view(), name='profile'),

    # 3. Корзина и Промокоды (Новая логика по пункту 5)
    path('cart/', CartView.as_view(), name='cart'),
    path('cart/items/', CartItemAddView.as_view(), name='cart-item-add'),
    path('cart/items/<int:pk>/', CartItemDetailView.as_view(), name='cart-item-detail'),
    path('cart/pay/', CartPayView.as_view(), name='cart-pay'),
    path('purchased/', PurchasedView.as_view(), name='purchased'),

    # 4. Кабинет организации (Заявки и просмотр)
    path('my-organization/', MyOrganizationView.as_view(), name='my-organization'),
    path('my-submission/', MySubmissionView.as_view(), name='my-sub'),
    path('submit-organization/', SubmitOrganizationView.as_view(), name='submit-org'),
    path('my-org-orders/', OrgOrdersView.as_view(), name='my-org-orders'),

    # 5. Админ-панель (Статистика и Модерация заявок)
    path('admin-stats/', AdminStatsView.as_view(), name='admin_stats'),
    path('admin/submissions/', PendingSubmissionsView.as_view(), name='pending-subs'),
    path('admin/submissions/<int:pk>/approve/', ApproveSubmissionView.as_view(), name='approve-sub'),
    path('admin/submissions/<int:pk>/reject/', RejectSubmissionView.as_view(), name='reject-sub'),
]
