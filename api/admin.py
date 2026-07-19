from django.contrib import admin
from .models import (
    User, Organization, OrganizationImage, Service, 
    ServiceImage, Order, OrderItem, OrganizationSubmission
)

class OrganizationImageInline(admin.TabularInline):
    model = OrganizationImage
    extra = 1

class ServiceImageInline(admin.TabularInline):
    model = ServiceImage
    extra = 1

class ServiceInline(admin.StackedInline):
    model = Service
    extra = 0
    fields = (
        'name', 'description', 'price', 'category', 
        'capacity', 'amenities', 'date_start', 
        'date_end', 'itinerary', 'included'
    )

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('is_redeemed',)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Упрощенный админ для пользователя во избежание конфликтов fieldsets"""
    list_display = ('username', 'email', 'role', 'is_staff', 'is_superuser', 'city')
    list_filter = ('role', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email')

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'org_type', 'city', 'is_verified')
    list_filter = ('is_verified', 'org_type')
    list_editable = ('is_verified',)
    inlines = [OrganizationImageInline, ServiceInline]

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'price', 'category')
    list_filter = ('organization', 'category')
    inlines = [ServiceImageInline]

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'is_paid', 'promo_code', 'created_at')
    list_filter = ('is_paid',)
    inlines = [OrderItemInline]

@admin.register(OrganizationSubmission)
class OrganizationSubmissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'org_type', 'submitted_by', 'status', 'created_at')
    list_filter = ('status', 'org_type')
    readonly_fields = ('created_at', 'reviewed_at')

admin.site.register(OrderItem)
