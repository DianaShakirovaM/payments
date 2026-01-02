import uuid
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class DurationChoices(models.TextChoices):
    """Варианты длительности скидок/купонов."""

    ONCE = 'once', 'Один раз'
    FOREVER = 'forever', 'Навсегда'
    REPEATING = 'repeating', 'Повторяющаяся'


class Currency(models.TextChoices):
    """Варианты налогов."""

    USD = 'usd', 'Dollar'
    EUR = 'eur', 'Euro'


class TaxType(models.TextChoices):
    """Варианты валют."""

    VAT = 'vat', 'VAT'
    SALES_TAX = 'sales_tax', 'Sales Tax'
    GST = 'gst', 'GST'


class Item(models.Model):
    """Товар."""

    name = models.CharField('Название', max_length=100)
    description = models.TextField('Описание')
    price = models.DecimalField(
        'Цена',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    currency = models.CharField(
        'Валюта',
        max_length=3,
        choices=Currency.choices,
        default=Currency.USD
    )

    def __str__(self):
        return f'{self.name} - {self.price} {self.currency}'

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'


class Discount(models.Model):
    """Скидка."""

    name = models.CharField('Название', max_length=100)
    percent_off = models.DecimalField(
        'Проценты',
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MinValueValidator(100)]
    )
    coupon_id = models.CharField('ID купона', max_length=100, blank=True)
    duration = models.CharField(
        'Длительность',
        max_length=20,
        choices=DurationChoices.choices,
        default=DurationChoices.ONCE
    )

    def __str__(self):
        return f'{self.name} - {self.percent_off}%'

    class Meta:
        verbose_name = 'Скидка'
        verbose_name_plural = 'Скидки'


class Tax(models.Model):
    """Налог."""

    name = models.CharField('Название', max_length=100)
    rate = models.DecimalField(
        'Ставка',
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    tax_type = models.CharField(
        'Тип',
        max_length=20,
        choices=TaxType.choices,
        default=TaxType.VAT
    )
    tax_id = models.CharField('ID налога', max_length=100, blank=True)
    country = models.CharField('Страна', max_length=2, default='US')

    def __str__(self):
        return f'{self.name} - {self.rate}%'

    class Meta:
        verbose_name = 'Налог'
        verbose_name_plural = 'Налоги'


class Order(models.Model):
    id = models.UUIDField(
        'ID заказа',
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    items = models.ManyToManyField(
        Item, verbose_name='Товары', through='OrderItem'
    )
    discount = models.ForeignKey(
        Discount,
        verbose_name='Скидка',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    tax = models.ForeignKey(
        Tax,
        verbose_name='Налог',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    payment_intent_id = models.CharField(
        'ID платежа',
        max_length=100,
        blank=True
    )

    def get_total_price(self):
        """Рассчитываеn общую сумму заказа"""
        total = Decimal('0')

        for order_item in self.order_items.all():
            total += order_item.item.price * order_item.quantity

        if self.tax:
            total += total * (self.tax.rate / Decimal('100'))

        if self.discount:
            total -= total * (self.discount.percent_off / Decimal('100'))

        return total

    def get_currency(self):
        items = self.items.all()

        if items.exists():
            return items.first().currency

        return Currency.USD

    def __str__(self):
        return f'{self.id} - {self.get_total_price():.2f}'

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'


class OrderItem(models.Model):
    """Промежуточная модель заказа и товара."""

    order = models.ForeignKey(
        Order,
        verbose_name='Заказ',
        on_delete=models.CASCADE,
        related_name='order_items'
    )
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('order', 'item')
