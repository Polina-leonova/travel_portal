from rest_framework import serializers
from .models import User, Organization, Service, Order

# 1. Сериализатор услуг
class ServiceSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source='organization.get_org_type_display', read_only=True)
    orgName = serializers.CharField(source='organization.name', read_only=True)
    serviceName = serializers.CharField(source='name', read_only=True)
    detail = serializers.CharField(source='description', read_only=True)
    qty = serializers.IntegerField(default=1, read_only=True) # Заглушка, если фронту нужно поле qty

    class Meta:
        model = Service
        fields = ['id', 'category', 'orgName', 'serviceName', 'detail', 'price', 'image', 'qty']

# 2. Сериализатор организации
class OrganizationSerializer(serializers.ModelSerializer):
    services = ServiceSerializer(many=True, read_only=True)
    class Meta:
        model = Organization
        fields = '__all__'

# 3. Сериализатор профиля (с полем is_staff для фронтенда)
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'gender', 'age', 'country', 'city', 'email', 'phone', 'role', 'is_staff']
        read_only_fields = ['role', 'is_staff']

# 4. Сериализатор заказов 
class OrderSerializer(serializers.ModelSerializer):
    items = ServiceSerializer(source='services', many=True, read_only=True)
    
    date = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'date', 'time', 'is_paid', 'promo_code', 'items', 'services']
        extra_kwargs = {
            'services': {'write_only': True}
        }

    def get_date(self, obj):
        return obj.created_at.strftime('%d.%m.%Y')

    def get_time(self, obj):
        return obj.created_at.strftime('%H:%M')

    # Валидация на 5 услуг, как просили в макете
    def validate_services(self, value):
        if len(value) > 5:
            raise serializers.ValidationError("В один заказ нельзя добавить больше 5 услуг.")
        return value

# 5. Статистика для админа
class AdminStatSerializer(serializers.Serializer):
    org_name = serializers.CharField()
    orders_count = serializers.IntegerField()
    total_sum = serializers.DecimalField(max_digits=12, decimal_places=2)

# 6. Регистрация
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'role', 'first_name', 'last_name']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data.get('email', ''),
            role=validated_data.get('role', 'buyer'),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
        return user
