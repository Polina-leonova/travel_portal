from rest_framework import serializers
from .models import User, Organization, OrganizationImage, Service, ServiceImage, Order, OrderItem, \
    OrganizationSubmission


class ServiceImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceImage
        fields = ['id', 'image']


class OrganizationBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'name', 'org_type']


class ServiceSerializer(serializers.ModelSerializer):
    organization_details = OrganizationBriefSerializer(source='organization', read_only=True)
    gallery = ServiceImageSerializer(many=True, read_only=True)

    class Meta:
        model = Service
        fields = [
            'id', 'organization', 'organization_details', 'category',
            'name', 'description', 'price', 'image', 'gallery',
            'capacity', 'amenities',
            'date_start', 'date_end', 'itinerary', 'included',
        ]


class OrganizationImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationImage
        fields = ['id', 'image']


class OrganizationSerializer(serializers.ModelSerializer):
    services = ServiceSerializer(many=True, read_only=True)
    gallery = OrganizationImageSerializer(many=True, read_only=True)

    class Meta:
        model = Organization
        fields = '__all__'


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'gender', 'age', 'country', 'city', 'email', 'phone', 'role', 'is_staff']
        read_only_fields = ['role', 'is_staff']


class OrderItemSerializer(serializers.ModelSerializer):
    service_details = ServiceSerializer(source='service', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'service', 'service_details', 'qty', 'is_redeemed']
        read_only_fields = ['is_redeemed']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'items', 'created_at', 'is_paid', 'promo_code']
        read_only_fields = ['user', 'items', 'is_paid', 'promo_code']


class OrganizationSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationSubmission
        fields = '__all__'
        read_only_fields = ['organization', 'submitted_by', 'status', 'admin_comment', 'created_at', 'reviewed_at']


class AdminStatSerializer(serializers.Serializer):
    org_name = serializers.CharField()
    orders_count = serializers.IntegerField()
    total_sum = serializers.DecimalField(max_digits=12, decimal_places=2)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'role', 'first_name', 'last_name']

    def validate_role(self, value):
        if value not in ('buyer', 'org'):
            raise serializers.ValidationError(
                "Через регистрацию можно завести только 'Покупателя' или 'Организацию'."
            )
        return value

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data.get('email', ''),
            role=validated_data.get('role', 'buyer'),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
