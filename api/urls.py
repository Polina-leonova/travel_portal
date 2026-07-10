from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import OrganizationViewSet, UserProfileView, OrderViewSet, AdminStatsView
from .views import RegisterView
from .views import CartView, PurchasedView, OrderViewSet
from .views import MyOrganizationView, MyServicesViewSet, OrgOrdersView

router = DefaultRouter()
router.register(r'organizations', OrganizationViewSet)
router.register(r'orders', OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
    # Авторизация
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Личный кабинет
    path('profile/', UserProfileView.as_view(), name='profile'),
    # Статистика для админа
    path('admin-stats/', AdminStatsView.as_view(), name='admin_stats'),
    path('register/', RegisterView.as_view(), name='register'),
    path('cart/', CartView.as_view(), name='cart'),
    path('purchased/', PurchasedView.as_view(), name='purchased'),
    # Путь для метода оплаты (pay)
    path('orders/<int:pk>/pay/', OrderViewSet.as_view({'post': 'pay'}), name='order-pay'),
    # Кабинет организации
    path('my-organization/', MyOrganizationView.as_view(), name='my-organization'),
    path('my-org-orders/', OrgOrdersView.as_view(), name='my-org-orders'),
]