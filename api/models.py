from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from django.core.validators import RegexValidator

# Валидатор проверяет, что номер начинается с + или цифры и содержит от 7 до 15 цифр
phone_regex = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message="Номер телефона должен быть в формате: '+999999999'. От 9 до 15 цифр."
)

class User(AbstractUser):
    ROLE_CHOICES = (
        ('buyer', 'Покупатель'),
        ('org', 'Организация'),
        ('admin', 'Администратор'),
    )
    role = models.CharField("Роль", max_length=10, choices=ROLE_CHOICES, default='buyer')
    phone = models.CharField("Телефон", max_length=20, validators=[phone_regex], blank=True, null=True)
    age = models.PositiveIntegerField("Возраст", blank=True, null=True)
    gender = models.CharField("Пол", max_length=10, choices=(('male', 'Мужской'), ('female', 'Женский')), blank=True)
    country = models.CharField("Страна", max_length=100, blank=True)
    city = models.CharField("Город", max_length=100, blank=True)


class Organization(models.Model):
    ORG_TYPES = (
        ('med_center', 'Медицинские центры'),
        ('beauty', 'Бьюти/SPA'),
        ('pharmacy', 'Фарма/Аптечные сети'),
        ('hotel', 'Отели'),
        ('sanatorium', 'Курорты/Санатории'),
        ('restaurant', 'Рестораны/Кафе'),
        ('tour_operator', 'Туроператоры/Турагентства'),
        ('sport', 'Спорт'),
    )

    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Владелец")
    name = models.CharField("Название", max_length=255)
    description = models.TextField("Описание", blank=True)
    org_type = models.CharField("Тип", max_length=20, choices=ORG_TYPES)

    federal_district = models.CharField("Федеральный округ", max_length=100)
    region = models.CharField("Область/Республика", max_length=100)
    city = models.CharField("Город", max_length=100)
    address = models.CharField("Адрес", max_length=255)
    latitude = models.DecimalField("Широта", max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField("Долгота", max_digits=9, decimal_places=6, blank=True, null=True)

    phone = models.CharField("Телефон организации", max_length=20, validators=[phone_regex])
    working_hours = models.CharField("Время работы", max_length=100, blank=True)
    is_verified = models.BooleanField("Подтверждено админом (Модерация)", default=False)
    image = models.ImageField("Главное фото", upload_to='orgs/', blank=True, null=True)

    # ["Скидка 10%", "Бесплатный завтрак"]
    perks = models.JSONField("Преференции для клиентов платформы", default=list, blank=True)
    # ["Телевизор", "Полотенца", "Кухня", "Зеркало", "Мини-бар"]
    general_amenities = models.JSONField("Услуги и удобства", default=list, blank=True)

    def __str__(self):
        return f"{self.name} ({self.get_org_type_display()})"


class OrganizationSubmission(models.Model):
    STATUS_CHOICES = (
        ('pending', 'На рассмотрении'),
        ('approved', 'Одобрено'),
        ('rejected', 'Отклонено'),
    )

    organization = models.ForeignKey(
        Organization, null=True, blank=True, on_delete=models.SET_NULL, related_name='submissions',
    )
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organization_submissions')

    org_type = models.CharField("Тип", max_length=20, choices=Organization.ORG_TYPES)
    name = models.CharField("Название", max_length=255)
    description = models.TextField("Описание", blank=True)
    federal_district = models.CharField("Федеральный округ", max_length=100)
    region = models.CharField("Область/Республика", max_length=100)
    city = models.CharField("Город", max_length=100)
    address = models.CharField("Адрес", max_length=255)
    latitude = models.DecimalField("Широта", max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField("Долгота", max_digits=9, decimal_places=6, blank=True, null=True)
    phone = models.CharField("Телефон организации", max_length=20, validators=[phone_regex])
    working_hours = models.CharField("Время работы", max_length=100, blank=True)
    image = models.ImageField("Главное фото", upload_to='org_submissions/', blank=True, null=True)
    perks = models.JSONField("Преференции для клиентов платформы", default=list, blank=True)
    general_amenities = models.JSONField("Услуги и удобства", default=list, blank=True)

    # список услуг-словарей: [{category, name, description, price, capacity,
    # amenities, date_start, date_end, itinerary, included}, ...]
    services_payload = models.JSONField("Услуги (черновик)", default=list, blank=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    admin_comment = models.TextField("Комментарий администратора", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"


class OrganizationImage(models.Model):
    organization = models.ForeignKey(Organization, related_name='gallery', on_delete=models.CASCADE)
    image = models.ImageField("Фото", upload_to='orgs/gallery/')

    def __str__(self):
        return f"Фото {self.organization.name}"


class Service(models.Model):
    # Универсальная услуга заполняются только для тех org_type, где они нужны
    organization = models.ForeignKey(Organization, related_name='services', on_delete=models.CASCADE)

    category = models.CharField(
        "Категория/раздел", max_length=150, blank=True,
        help_text="Заголовок группы: 'Гастроэнтерология', 'Стандарт', 'Испания-Италия'",
    )

    name = models.CharField("Название услуги", max_length=255)
    description = models.TextField("Подробное описание", blank=True)
    price = models.DecimalField("Цена (конкретная)", max_digits=10, decimal_places=2)
    image = models.ImageField("Фото услуги", upload_to='services/', blank=True, null=True)

    # --- номера отеля/санатория/спорт-базы ---
    capacity = models.PositiveIntegerField("Вместимость (человек)", blank=True, null=True)
    amenities = models.JSONField("Состав номера", default=list, blank=True)

    # --- туры у туроператоров ---
    date_start = models.DateField("Дата начала тура", blank=True, null=True)
    date_end = models.DateField("Дата окончания тура", blank=True, null=True)
    itinerary = models.JSONField("Программа по дням", default=list, blank=True)
    included = models.JSONField("Что включено в тур", default=list, blank=True)

    def __str__(self):
        return f"{self.name} - {self.organization.name}"


class ServiceImage(models.Model):
    service = models.ForeignKey(Service, related_name='gallery', on_delete=models.CASCADE)
    image = models.ImageField("Фото", upload_to='services/gallery/')

    def __str__(self):
        return f"Фото {self.service.name}"


class Review(models.Model):
    STATUS_CHOICES = (
        ('pending', 'На рассмотрении'),
        ('approved', 'Одобрено'),
        ('rejected', 'Отклонено'),
    )

    organization = models.ForeignKey(Organization, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(
        "Оценка", choices=[(i, str(i)) for i in range(1, 6)],
    )
    text = models.TextField("Текст отзыва", blank=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('organization', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} → {self.organization.name} ({self.rating})"


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField("Оплачено (10% платформе)", default=False)
    promo_code = models.CharField("Промокод для скидки", max_length=10, unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.is_paid and not self.promo_code:
            self.promo_code = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    qty = models.PositiveIntegerField("Количество", default=1)
    is_redeemed = models.BooleanField("Промокод погашен организацией", default=False)

    class Meta:
        unique_together = ('order', 'service')

    def __str__(self):
        return f"{self.service.name} x{self.qty} ({self.order_id})"
