from django.contrib import admin
from .models import Product, Supplier, Warehouse, Stock, PurchaseOrder, PurchaseOrderItem, Sale, SaleItem


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'price', 'unit', 'created_at']
    search_fields = ['name', 'sku', 'description']
    list_filter = ['unit']


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'email', 'phone', 'created_at']
    search_fields = ['name', 'contact_person', 'email']


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['name', 'address', 'created_at']
    search_fields = ['name', 'address']


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['warehouse', 'product', 'quantity', 'updated_at']
    list_filter = ['warehouse']
    search_fields = ['product__name', 'product__sku']


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'supplier', 'status', 'order_date', 'total_amount', 'received_date']
    list_filter = ['status', 'supplier']
    search_fields = ['order_number', 'supplier__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ['purchase_order', 'product', 'quantity', 'price', 'total', 'received_quantity']
    list_filter = ['purchase_order']


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['sale_number', 'sale_date', 'customer_name', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'sale_date']
    search_fields = ['sale_number', 'customer_name', 'customer_email']
    readonly_fields = ['created_at']


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ['sale', 'product', 'quantity', 'price', 'total']
    list_filter = ['sale']
