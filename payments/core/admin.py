from django.contrib import admin

from .models import Discount, Item, Order, OrderItem, Tax


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'currency')
    search_fields = ('name',)


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ('name', 'percent_off', 'duration')


@admin.register(Tax)
class TaxAdmin(admin.ModelAdmin):
    list_display = ('name', 'rate', 'tax_type', 'country')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'get_total_price', 'get_currency')
    inlines = (OrderItemInline,)
    list_filter = ('created_at',)

    @admin.display(description='Общая сумма')
    def get_total_price(self, obj):
        return f'{obj.get_total_price():.2f}'

    @admin.display(description='Валюта')
    def get_currency(self, obj):
        return obj.get_currency()
