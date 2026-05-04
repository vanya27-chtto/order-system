from django.db import models
from django.core.validators import MinValueValidator, EmailValidator
from django.utils import timezone


class Product(models.Model):
    """Справочник товаров"""
    name = models.CharField(max_length=255, verbose_name="Наименование товара")
    sku = models.CharField(max_length=100, unique=True, verbose_name="Артикул (SKU)")
    description = models.TextField(blank=True, verbose_name="Описание")
    unit = models.CharField(max_length=50, default='шт', verbose_name="Единица измерения")
    price = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        verbose_name="Цена"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.sku})"


class Supplier(models.Model):
    """Поставщики"""
    name = models.CharField(max_length=255, verbose_name="Название поставщика")
    contact_person = models.CharField(max_length=255, blank=True, verbose_name="Контактное лицо")
    email = models.EmailField(validators=[EmailValidator()], verbose_name="Email")
    phone = models.CharField(max_length=50, blank=True, verbose_name="Телефон")
    address = models.TextField(blank=True, verbose_name="Адрес")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Поставщик"
        verbose_name_plural = "Поставщики"
        ordering = ['name']

    def __str__(self):
        return self.name


class Warehouse(models.Model):
    """Склад товаров"""
    name = models.CharField(max_length=255, verbose_name="Название склада")
    address = models.TextField(blank=True, verbose_name="Адрес склада")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Склад"
        verbose_name_plural = "Склады"
        ordering = ['name']

    def __str__(self):
        return self.name


class Stock(models.Model):
    """Остатки товаров на складе"""
    warehouse = models.ForeignKey(
        Warehouse, 
        on_delete=models.CASCADE, 
        related_name='stocks',
        verbose_name="Склад"
    )
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='stocks',
        verbose_name="Товар"
    )
    quantity = models.PositiveIntegerField(default=0, verbose_name="Количество")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Остаток на складе"
        verbose_name_plural = "Остатки на складах"
        unique_together = ['warehouse', 'product']
        ordering = ['warehouse', 'product']

    def __str__(self):
        return f"{self.warehouse} - {self.product}: {self.quantity}"


class PurchaseOrder(models.Model):
    """Заявки на закупку"""
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('sent', 'Отправлен'),
        ('confirmed', 'Подтвержден'),
        ('received', 'Получен'),
        ('cancelled', 'Отменен'),
    ]

    supplier = models.ForeignKey(
        Supplier, 
        on_delete=models.PROTECT, 
        related_name='purchase_orders',
        verbose_name="Поставщик"
    )
    order_number = models.CharField(max_length=50, unique=True, verbose_name="Номер заказа")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="Статус")
    order_date = models.DateField(default=timezone.now, verbose_name="Дата заказа")
    expected_delivery_date = models.DateField(null=True, blank=True, verbose_name="Ожидаемая дата поставки")
    received_date = models.DateField(null=True, blank=True, verbose_name="Дата получения")
    total_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Общая сумма"
    )
    notes = models.TextField(blank=True, verbose_name="Примечание")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Заявка на закупку"
        verbose_name_plural = "Заявки на закупку"
        ordering = ['-order_date']

    def __str__(self):
        return f"Заказ {self.order_number} от {self.supplier}"


class PurchaseOrderItem(models.Model):
    """Позиции заявки на закупку"""
    purchase_order = models.ForeignKey(
        PurchaseOrder, 
        on_delete=models.CASCADE, 
        related_name='items',
        verbose_name="Заявка на закупку"
    )
    product = models.ForeignKey(
        Product, 
        on_delete=models.PROTECT, 
        related_name='purchase_order_items',
        verbose_name="Товар"
    )
    quantity = models.PositiveIntegerField(verbose_name="Количество")
    price = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        verbose_name="Цена за единицу"
    )
    total = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        editable=False,
        verbose_name="Сумма"
    )
    received_quantity = models.PositiveIntegerField(default=0, verbose_name="Получено")

    class Meta:
        verbose_name = "Позиция заявки на закупку"
        verbose_name_plural = "Позиции заявок на закупку"

    def __str__(self):
        return f"{self.product} - {self.quantity}"

    def save(self, *args, **kwargs):
        self.total = self.quantity * self.price
        super().save(*args, **kwargs)


class Sale(models.Model):
    """Продажи"""
    STATUS_CHOICES = [
        ('completed', 'Завершен'),
        ('cancelled', 'Отменен'),
    ]

    sale_number = models.CharField(max_length=50, unique=True, verbose_name="Номер продажи")
    sale_date = models.DateTimeField(default=timezone.now, verbose_name="Дата продажи")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed', verbose_name="Статус")
    total_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Общая сумма"
    )
    customer_name = models.CharField(max_length=255, blank=True, verbose_name="Клиент")
    customer_email = models.EmailField(blank=True, verbose_name="Email клиента")
    customer_phone = models.CharField(max_length=50, blank=True, verbose_name="Телефон клиента")
    notes = models.TextField(blank=True, verbose_name="Примечание")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Продажа"
        verbose_name_plural = "Продажи"
        ordering = ['-sale_date']

    def __str__(self):
        return f"Продажа {self.sale_number} от {self.sale_date}"


class SaleItem(models.Model):
    """Позиции продажи"""
    sale = models.ForeignKey(
        Sale, 
        on_delete=models.CASCADE, 
        related_name='items',
        verbose_name="Продажа"
    )
    product = models.ForeignKey(
        Product, 
        on_delete=models.PROTECT, 
        related_name='sale_items',
        verbose_name="Товар"
    )
    quantity = models.PositiveIntegerField(verbose_name="Количество")
    price = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        verbose_name="Цена за единицу"
    )
    total = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        editable=False,
        verbose_name="Сумма"
    )

    class Meta:
        verbose_name = "Позиция продажи"
        verbose_name_plural = "Позиции продаж"

    def __str__(self):
        return f"{self.product} - {self.quantity}"

    def save(self, *args, **kwargs):
        self.total = self.quantity * self.price
        super().save(*args, **kwargs)
