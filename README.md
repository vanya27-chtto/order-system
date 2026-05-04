# Система управления складом и продажами

## Описание
Django-приложение для управления складом, продажами и закупками товаров с использованием PostgreSQL.

## Структура базы данных

### Таблицы:

1. **Product (Товары)** - справочник товаров
   - name - наименование товара
   - sku - артикул (уникальный)
   - description - описание
   - unit - единица измерения
   - price - цена
   - created_at, updated_at - даты создания и обновления

2. **Supplier (Поставщики)**
   - name - название поставщика
   - contact_person - контактное лицо
   - email - email для связи
   - phone - телефон
   - address - адрес

3. **Warehouse (Склады)**
   - name - название склада
   - address - адрес склада

4. **Stock (Остатки на складе)**
   - warehouse - ссылка на склад
   - product - ссылка на товар
   - quantity - количество
   - unique_together: [warehouse, product]

5. **PurchaseOrder (Заявки на закупку)**
   - supplier - поставщик
   - order_number - номер заказа (уникальный)
   - status - статус (draft/sent/confirmed/received/cancelled)
   - order_date - дата заказа
   - expected_delivery_date - ожидаемая дата поставки
   - received_date - дата получения
   - total_amount - общая сумма

6. **PurchaseOrderItem (Позиции заявки на закупку)**
   - purchase_order - ссылка на заявку
   - product - товар
   - quantity - количество
   - price - цена за единицу
   - total - сумма позиции
   - received_quantity - получено

7. **Sale (Продажи)**
   - sale_number - номер продажи (уникальный)
   - sale_date - дата продажи
   - status - статус (completed/cancelled)
   - total_amount - общая сумма
   - customer_name, customer_email, customer_phone - данные клиента

8. **SaleItem (Позиции продажи)**
   - sale - ссылка на продажу
   - product - товар
   - quantity - количество
   - price - цена за единицу
   - total - сумма позиции

## Функционал

### 1. Управление товарами (Product)
- Создание, редактирование, удаление товаров
- Просмотр списка товаров с поиском по названию и SKU

### 2. Управление складом (Stock)
- Просмотр остатков по каждому складу
- Автоматическое обновление при продажах и закупках

### 3. Продажи (Sale)
- Оформление продажи с автоматическим списанием товаров со склада
- Проверка наличия товара перед продажей
- Использование `SaleService.create_sale()` для создания продажи

### 4. Поставщики (Supplier)
- Хранение контактных данных поставщиков
- Возможность отправки заказа на email

### 5. Заявки на закупку (PurchaseOrder)
- Создание заявки в статусе "Черновик"
- Отправка заказа поставщику по email (`PurchaseOrderService.send_to_supplier()`)
- Подтверждение получения товара с пополнением склада (`PurchaseOrderService.confirm_receipt()`)

## Сервисы

### StockService
- `get_stock(product, warehouse)` - получить остаток товара
- `reserve_stock(product, warehouse, quantity)` - зарезервировать товар (списание)
- `add_stock(product, warehouse, quantity)` - пополнить склад

### SaleService
- `create_sale(sale_data, items_data, warehouse)` - создать продажу со списанием товаров

### PurchaseOrderService
- `create_purchase_order(supplier, items, order_number)` - создать заявку на закупку
- `send_to_supplier(purchase_order)` - отправить заказ поставщику по email
- `confirm_receipt(purchase_order, warehouse, received_items)` - подтвердить получение и пополнить склад

## Настройка

### 1. База данных PostgreSQL
В `settings.py` настроено подключение к PostgreSQL:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'inventory_db',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

Создайте базу данных:
```sql
CREATE DATABASE inventory_db;
```

### 2. Email для отправки заказов
В `settings.py` настройте SMTP:
```python
EMAIL_HOST = 'smtp.example.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your_email@example.com'
EMAIL_HOST_PASSWORD = 'your_password'
DEFAULT_FROM_EMAIL = 'inventory@example.com'
```

### 3. Миграции
```bash
python manage.py migrate
```

### 4. Запуск сервера
```bash
python manage.py runserver
```

### 5. Админка
Доступна по адресу `/admin/`

## Примеры использования

### Создание продажи:
```python
from warehouse.services import SaleService
from warehouse.models import Product, Warehouse

warehouse = Warehouse.objects.first()
product = Product.objects.get(sku='SKU001')

sale_data = {
    'customer_name': 'Иван Иванов',
    'customer_email': 'ivan@example.com',
}

items_data = [
    {'product': product, 'quantity': 2, 'price': 100.00},
]

sale = SaleService.create_sale(sale_data, items_data, warehouse)
```

### Создание и отправка заказа поставщику:
```python
from warehouse.services import PurchaseOrderService
from warehouse.models import Supplier, Product

supplier = Supplier.objects.get(email='supplier@example.com')
product = Product.objects.get(sku='SKU001')

items = [
    {'product': product, 'quantity': 100, 'price': 50.00},
]

order = PurchaseOrderService.create_purchase_order(supplier, items)
order = PurchaseOrderService.send_to_supplier(order)
```

### Подтверждение получения заказа:
```python
from warehouse.services import PurchaseOrderService
from warehouse.models import Warehouse

warehouse = Warehouse.objects.get(name='Основной склад')
order = PurchaseOrder.objects.get(order_number='PO-00001')

PurchaseOrderService.confirm_receipt(order, warehouse)
```
