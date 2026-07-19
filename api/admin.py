from django.contrib import admin
from .models import User, Organization, OrganizationImage, Service, ServiceImage, Order, OrderItem, \
    OrganizationSubmission, Review


class OrganizationImageInline(admin.TabularInline):
    model = OrganizationImage
    extra = 1


class ServiceImageInline(admin.TabularInline):
    model = ServiceImage
    extra = 1


class ServiceInline(admin.StackedInline):
    model = Service
    extra = 1
    fields = (
        'category', 'name', 'description', 'price', 'image',
        ('capacity', 'amenities'),
        ('date_start', 'date_end'),
        'itinerary', 'included',
    )


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'org_type', 'city', 'is_verified')
    list_filter = ('is_verified', 'org_type')
    list_editable = ('is_verified',)
    inlines = [OrganizationImageInline, ServiceInline]


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'organization', 'price')
    list_filter = ('organization',)
    inlines = [ServiceImageInline]


@admin.register(OrganizationSubmission)
class OrganizationSubmissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'org_type', 'submitted_by', 'status', 'created_at')
    list_filter = ('status', 'org_type')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'promo_code', 'is_paid')
    inlines = [OrderItemInline]


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_staff', 'is_superuser', 'city')
    list_filter = ('role', 'is_staff', 'is_superuser')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('organization', 'user', 'rating', 'status', 'created_at')
    list_filter = ('status', 'rating')
