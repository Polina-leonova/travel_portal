from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

# 1. Пользователь
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

# 2. Организация
class Organization(models.Model):
    ORG_TYPES = (
        ('med_center', 'Медицинский центр'),
        ('beauty', 'Красота и здоровье'),
        ('pharmacy', 'Аптека'),
        ('hotel', 'Гостиница'),
        ('sanatorium', 'Санаторий'),
        ('restaurant', 'Ресторан'),
        ('tour_operator', 'Туроператор'),
        ('sport', 'Спортивный туризм'),
    )
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Владелец")
    name = models.CharField("Название", max_length=255)
    description = models.TextField("Описание", blank=True)
    org_type = models.CharField("Тип", max_length=20, choices=ORG_TYPES)
    
    perks = models.JSONField("Преференции для клиентов", default=list, blank=True)
    general_amenities = models.JSONField("Услуги и удобства", default=list, blank=True)
    
    federal_district = models.CharField("Федеральный округ", max_length=100)
    region = models.CharField("Область/Республика", max_length=100)
    city = models.CharField("Город", max_length=100)
    address = models.CharField("Адрес", max_length=255)
    
    phone = models.CharField("Телефон организации", max_length=20)
    working_hours = models.CharField("Время работы", max_length=100, blank=True)
    is_verified = models.BooleanField("Модерация пройдена", default=False)
    image = models.ImageField("Главное фото", upload_to='orgs/', blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.get_org_type_display()})"

class OrganizationImage(models.Model):
    organization = models.ForeignKey(Organization, related_name='gallery', on_delete=models.CASCADE)
    image = models.ImageField("Фото", upload_to='orgs/gallery/')

# 3. Услуги
class Service(models.Model):
    organization = models.ForeignKey(Organization, related_name='services', on_delete=models.CASCADE)
    name = models.CharField("Название услуги", max_length=255)
    description = models.TextField("Описание", blank=True)
    price = models.DecimalField("Цена", max_digits=10, decimal_places=2)
    image = models.ImageField("Фото услуги", upload_to='services/', blank=True, null=True)
  
    category = models.CharField("Категория", max_length=100, blank=True)
    capacity = models.PositiveIntegerField("Вместимость / Кол-во", default=1)
    amenities = models.JSONField("Состав / Удобства", default=list, blank=True)
  
    date_start = models.DateField("Дата начала", null=True, blank=True)
    date_end = models.DateField("Дата окончания", null=True, blank=True)
    itinerary = models.JSONField("Программа по дням", default=list, blank=True)
    included = models.JSONField("Что включено", default=list, blank=True)

    def __str__(self):
        return f"{self.name} - {self.organization.name}"

class ServiceImage(models.Model):
    service = models.ForeignKey(Service, related_name='gallery', on_delete=models.CASCADE)
    image = models.ImageField("Фото", upload_to='services/gallery/')

# 4. Заказы 
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField("Оплачено", default=False)
    promo_code = models.CharField("Промокод", max_length=10, unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Генерируем промокод только при факте оплаты
        if self.is_paid and not self.promo_code:
            self.promo_code = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    qty = models.PositiveIntegerField("Количество", default=1)
    is_redeemed = models.BooleanField("Промокод погашен", default=False)

    class Meta:
        unique_together = ('order', 'service')

# 5. Заявки на модерацию
class OrganizationSubmission(models.Model):
    STATUS_CHOICES = (
        ('pending', 'На рассмотрении'),
        ('approved', 'Одобрено'),
        ('rejected', 'Отклонено'),
    )
    
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField("Название из заявки", max_length=255)
    org_type = models.CharField("Тип", max_length=20, choices=Organization.ORG_TYPES)
    
    # Все данные организации в черновике
    org_data = models.JSONField("Данные организации")
    services_payload = models.JSONField("Список услуг (черновик)", default=list)
    
    status = models.CharField("Статус", max_length=10, choices=STATUS_CHOICES, default='pending')
    admin_comment = models.TextField("Комментарий админа", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField("Дата проверки", null=True, blank=True)

    def __str__(self):
        return f"Заявка: {self.name} [{self.get_status_display()}]"
