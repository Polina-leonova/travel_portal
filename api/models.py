from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

# 1. Пользователь (Покупатель, Организация, Админ)
class User(AbstractUser):
    ROLE_CHOICES = (
        ('buyer', 'Покупатель'),
        ('org', 'Организация'),
        ('admin', 'Администратор'),
    )
    role = models.CharField("Роль", max_length=10, choices=ROLE_CHOICES, default='buyer')
    phone = models.CharField("Телефон", max_length=20, blank=True, null=True)
    age = models.PositiveIntegerField("Возраст", blank=True, null=True)
    gender = models.CharField("Пол", max_length=10, choices=(('male', 'Мужской'), ('female', 'Женский')), blank=True)
    country = models.CharField("Страна", max_length=100, blank=True)
    city = models.CharField("Город", max_length=100, blank=True)

# 2. Организация (Отели, Медцентры, Рестораны и т.д.)
class Organization(models.Model):
    ORG_TYPES = (
        ('pharmacy', 'Аптека'),
        ('restaurant', 'Ресторан'),
        ('hotel', 'Гостиница'),
        ('transport', 'Транспортная компания'),
        ('med_center', 'Медицинский центр'),
        ('sport', 'Спортивный туризм'),
        ('sanatorium', 'Санаторий'),
    )
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Владелец")
    name = models.CharField("Название", max_length=255)
    description = models.TextField("Описание", blank=True)
    org_type = models.CharField("Тип", max_length=20, choices=ORG_TYPES)

    amenities = models.TextField("Удобства и услуги (для отелей)", blank=True)
    map_link = models.TextField("Ссылка на карту или координаты", blank=True)
    
    # Поле для отзывов (пока просто строка или можно оставить на будущее)
    reviews_count = models.PositiveIntegerField("Кол-во отзывов", default=0)
    # География 
    federal_district = models.CharField("Федеральный округ", max_length=100)
    region = models.CharField("Область/Республика", max_length=100)
    city = models.CharField("Город", max_length=100)
    address = models.CharField("Адрес", max_length=255)
    
    phone = models.CharField("Телефон организации", max_length=20)
    working_hours = models.CharField("Время работы", max_length=100, blank=True)
    is_verified = models.BooleanField("Подтверждено админом (Модерация)", default=False)
    image = models.ImageField("Главное фото", upload_to='orgs/', blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.get_org_type_display()})"

# 3. Услуги (конкретные номера отелей, процедуры в медцентрах)
class Service(models.Model):
    organization = models.ForeignKey(Organization, related_name='services', on_delete=models.CASCADE)
    name = models.CharField("Название услуги", max_length=255)
    description = models.TextField("Подробное описание", blank=True)
    price = models.DecimalField("Цена (конкретная)", max_digits=10, decimal_places=2)
    image = models.ImageField("Фото услуги", upload_to='services/', blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.organization.name}"

# 4. Заказы (Корзина и оплаченные услуги)
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    services = models.ManyToManyField(Service, verbose_name="Услуги")
    created_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField("Оплачено (10% платформе)", default=False)
    promo_code = models.CharField("Промокод для скидки", max_length=10, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.promo_code:
            self.promo_code = str(uuid.uuid4())[:8].upper() # Генерация промокода
        super().save(*args, **kwargs)
