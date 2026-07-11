from rest_framework import serializers
from .models import User, Organization, Service, Order

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'

class OrganizationSerializer(serializers.ModelSerializer):
    services = ServiceSerializer(many=True, read_only=True)
    class Meta:
        model = Organization
        fields = '__all__'

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'gender', 'age', 'country', 'city', 'email', 'phone', 'role', 'is_staff']
        read_only_fields = ['role', 'is_staff']

class OrderSerializer(serializers.ModelSerializer):
    service_details = ServiceSerializer(source='services', many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'services', 'service_details', 'created_at', 'is_paid', 'promo_code']
        read_only_fields = ['user', 'promo_code', 'is_paid']

    def validate_services(self, value):
        if len(value) > 5:
            raise serializers.ValidationError("В один заказ нельзя добавить больше 5 услуг.")
        return value

# Для админки: статистика
class AdminStatSerializer(serializers.Serializer):
    org_name = serializers.CharField()
    orders_count = serializers.IntegerField()
    total_sum = serializers.DecimalField(max_digits=12, decimal_places=2)

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'role', 'first_name', 'last_name']

    def create(self, validated_data):
        # Метод create нужен, чтобы правильно зашифровать пароль
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data.get('email', ''),
            role=validated_data.get('role', 'buyer'), # По умолчанию - покупатель
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
        return user    
