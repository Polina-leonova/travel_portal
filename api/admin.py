from django.contrib import admin
from .models import User, Organization, Service, Order
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# Класс для отображения услуг внутри организации
class ServiceInline(admin.TabularInline):
    model = Service
    extra = 1 # Сколько пустых строк для новых услуг показывать сразу

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'org_type', 'city', 'is_verified')
    list_filter = ('is_verified', 'org_type')
    list_editable = ('is_verified',)
    inlines = [ServiceInline]

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'price')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'promo_code', 'is_paid')

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'role', 'city', 'is_staff')
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительная информация', {'fields': ('role', 'phone', 'age', 'gender', 'country', 'city')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Дополнительная информация', {'fields': ('role', 'phone', 'age', 'gender', 'country', 'city')}),
    )
