from django.db import models
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from .models import Product, Supplier, Warehouse, Stock, PurchaseOrder, PurchaseOrderItem, Sale, SaleItem


class StockService:
    """Сервис для управления складскими остатками"""

    @staticmethod
    def get_stock(product, warehouse=None):
        """Получить остаток товара на складе"""
        if warehouse:
            stock = Stock.objects.filter(product=product, warehouse=warehouse).first()
            return stock.quantity if stock else 0
        else:
            # Общий остаток по всем складам
            stocks = Stock.objects.filter(product=product)
            return sum(stock.quantity for stock in stocks)

    @staticmethod
    @transaction.atomic
    def reserve_stock(product, warehouse, quantity):
        """Резервирование товара на складе (перед продажей)"""
        stock, created = Stock.objects.get_or_create(
            product=product, 
            warehouse=warehouse,
            defaults={'quantity': 0}
        )
        
        if stock.quantity < quantity:
            raise ValueError(f"Недостаточно товара {product.name} на складе {warehouse.name}")
        
        stock.quantity -= quantity
        stock.save()
        return stock

    @staticmethod
    @transaction.atomic
    def add_stock(product, warehouse, quantity):
        """Пополнение склада"""
        stock, created = Stock.objects.get_or_create(
            product=product, 
            warehouse=warehouse,
            defaults={'quantity': 0}
        )
        
        stock.quantity += quantity
        stock.save()
        return stock


class SaleService:
    """Сервис для управления продажами"""

    @staticmethod
    @transaction.atomic
    def create_sale(sale_data, items_data, warehouse):
        """
        Создание продажи с автоматическим списанием товаров со склада
        
        Args:
            sale_data: dict с данными продажи (customer_name, customer_email, etc.)
            items_data: list [{'product': Product, 'quantity': int, 'price': Decimal}, ...]
            warehouse: Warehouse объект склада
        """
        # Создаем продажу
        sale = Sale.objects.create(
            sale_number=sale_data.get('sale_number', Sale.objects.count() + 1),
            customer_name=sale_data.get('customer_name', ''),
            customer_email=sale_data.get('customer_email', ''),
            customer_phone=sale_data.get('customer_phone', ''),
            notes=sale_data.get('notes', ''),
        )
        
        total_amount = 0
        
        for item_data in items_data:
            product = item_data['product']
            quantity = item_data['quantity']
            price = item_data['price']
            
            # Проверяем наличие товара
            current_stock = StockService.get_stock(product, warehouse)
            if current_stock < quantity:
                # Отменяем продажу если товара недостаточно
                sale.delete()
                raise ValueError(f"Недостаточно товара {product.name} на складе")
            
            # Списываем товар со склада
            StockService.reserve_stock(product, warehouse, quantity)
            
            # Создаем позицию продажи
            sale_item = SaleItem.objects.create(
                sale=sale,
                product=product,
                quantity=quantity,
                price=price,
                total=quantity * price
            )
            
            total_amount += sale_item.total
        
        sale.total_amount = total_amount
        sale.save()
        
        return sale


class PurchaseOrderService:
    """Сервис для управления заказами поставщикам"""

    @staticmethod
    def create_purchase_order(supplier, items, order_number=None):
        """
        Создание заявки на закупку
        
        Args:
            supplier: Supplier объект
            items: list [{'product': Product, 'quantity': int, 'price': Decimal}, ...]
            order_number: str номер заказа (если не указан, генерируется автоматически)
        """
        if not order_number:
            order_number = f"PO-{PurchaseOrder.objects.count() + 1:05d}"
        
        purchase_order = PurchaseOrder.objects.create(
            supplier=supplier,
            order_number=order_number,
            status='draft'
        )
        
        total_amount = 0
        
        for item_data in items:
            product = item_data['product']
            quantity = item_data['quantity']
            price = item_data['price']
            
            purchase_order_item = PurchaseOrderItem.objects.create(
                purchase_order=purchase_order,
                product=product,
                quantity=quantity,
                price=price,
                total=quantity * price
            )
            
            total_amount += purchase_order_item.total
        
        purchase_order.total_amount = total_amount
        purchase_order.save()
        
        return purchase_order

    @staticmethod
    def send_to_supplier(purchase_order):
        """
        Отправка заказа поставщику по email
        
        Args:
            purchase_order: PurchaseOrder объект
        """
        if purchase_order.status != 'draft':
            raise ValueError("Можно отправить только заказ в статусе 'Черновик'")
        
        supplier = purchase_order.supplier
        
        # Формируем письмо
        subject = f"Заказ на поставку №{purchase_order.order_number}"
        
        message = f"""
        Уважаемый {supplier.contact_person or supplier.name}!
        
        Просим поставить следующие товары:
        
        """
        
        for item in purchase_order.items.all():
            message += f"- {item.product.name}: {item.quantity} шт. по {item.price} руб. (сумма: {item.total} руб.)\n"
        
        message += f"""
        
        Общая сумма заказа: {purchase_order.total_amount} руб.
        
        Ожидаемая дата поставки: {purchase_order.expected_delivery_date or 'не указана'}
        
        С уважением,
        Ваша компания
        """
        
        # Отправляем email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[supplier.email],
            fail_silently=False,
        )
        
        # Обновляем статус
        purchase_order.status = 'sent'
        purchase_order.save()
        
        return purchase_order

    @staticmethod
    @transaction.atomic
    def confirm_receipt(purchase_order, warehouse, received_items=None):
        """
        Подтверждение получения заказа и пополнение склада
        
        Args:
            purchase_order: PurchaseOrder объект
            warehouse: Warehouse объект склада для пополнения
            received_items: dict {product_id: received_quantity} - если не указано, принимаем всё
        """
        if purchase_order.status not in ['sent', 'confirmed']:
            raise ValueError("Нельзя подтвердить заказ в текущем статусе")
        
        if received_items is None:
            # Принимаем все товары в полном объеме
            for item in purchase_order.items.all():
                StockService.add_stock(item.product, warehouse, item.quantity)
                item.received_quantity = item.quantity
                item.save()
        else:
            # Принимаем частично
            for item in purchase_order.items.all():
                received_qty = received_items.get(item.product.id, 0)
                if received_qty > item.quantity:
                    raise ValueError(f"Получено больше товара {item.product.name}, чем заказано")
                
                StockService.add_stock(item.product, warehouse, received_qty)
                item.received_quantity = received_qty
                item.save()
        
        purchase_order.status = 'received'
        purchase_order.received_date = timezone.now().date()
        purchase_order.save()
        
        return purchase_order
