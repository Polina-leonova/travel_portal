from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    OrganizationViewSet, UserProfileView, AdminStatsView, RegisterView,
    CartView, CartItemAddView, CartItemDetailView, CartPayView, PurchasedView,
    MyOrganizationView, MySubmissionView, SubmitOrganizationView, OrgOrdersView,
    PendingSubmissionsView, ApproveSubmissionView, RejectSubmissionView,
    ReviewListView, SubmitReviewView, MyReviewView,
    PendingReviewsView, ApproveReviewView, RejectReviewView, AdminReviewDeleteView, AllReviewsView,
)

router = DefaultRouter()
router.register(r'organizations', OrganizationViewSet)

urlpatterns = [
    path('', include(router.urls)),

    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='register'),

    path('profile/', UserProfileView.as_view(), name='profile'),
    path('admin-stats/', AdminStatsView.as_view(), name='admin_stats'),

    path('cart/', CartView.as_view(), name='cart'),
    path('cart/items/', CartItemAddView.as_view(), name='cart-item-add'),
    path('cart/items/<int:pk>/', CartItemDetailView.as_view(), name='cart-item-detail'),
    path('cart/pay/', CartPayView.as_view(), name='cart-pay'),

    path('purchased/', PurchasedView.as_view(), name='purchased'),

    path('my-organization/', MyOrganizationView.as_view(), name='my-organization'),
    path('my-submission/', MySubmissionView.as_view(), name='my-submission'),
    path('submit-organization/', SubmitOrganizationView.as_view(), name='submit-organization'),
    path('my-org-orders/', OrgOrdersView.as_view(), name='my-org-orders'),

    path('admin/submissions/', PendingSubmissionsView.as_view(), name='admin-submissions'),
    path('admin/submissions/<int:pk>/approve/', ApproveSubmissionView.as_view(), name='admin-submission-approve'),
    path('admin/submissions/<int:pk>/reject/', RejectSubmissionView.as_view(), name='admin-submission-reject'),

    path('reviews/', ReviewListView.as_view(), name='reviews'),
    path('submit-review/', SubmitReviewView.as_view(), name='submit-review'),
    path('my-review/', MyReviewView.as_view(), name='my-review'),

    path('admin/reviews/', PendingReviewsView.as_view(), name='admin-reviews'),
    path('admin/reviews/all/', AllReviewsView.as_view(), name='admin-reviews-all'),
    path('admin/reviews/<int:pk>/approve/', ApproveReviewView.as_view(), name='admin-review-approve'),
    path('admin/reviews/<int:pk>/reject/', RejectReviewView.as_view(), name='admin-review-reject'),
    path('admin/reviews/<int:pk>/delete/', AdminReviewDeleteView.as_view(), name='admin-review-delete'),
]
