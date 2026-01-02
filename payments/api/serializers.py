from rest_framework import serializers

from core.models import Item, Order, OrderItem


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ('id', 'name', 'description', 'price', 'currency')


class OrderItemSerializer(serializers.ModelSerializer):
    """Сериализатор для элементов заказа."""

    item_id = serializers.PrimaryKeyRelatedField(
        queryset=Item.objects.all(),
        source='item'
    )

    class Meta:
        model = OrderItem
        fields = ('item_id', 'quantity')
        extra_kwargs = {
            'quantity': {'min_value': 1}
        }


class OrderSerializer(serializers.ModelSerializer):
    """Сериализатор для заказа."""

    items = OrderItemSerializer(many=True, write_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            'id', 'items', 'discount', 'tax', 'total_price', 'created_at')
        read_only_fields = ['id', 'total_price', 'created_at']

    def get_total_price(self, obj):
        """Рассчитывает общую сумму заказа"""
        return obj.get_total_price()

    def create(self, validated_data):
        """Создание заказа с элементами"""
        items_data = validated_data.pop('items', [])
        # Создаем заказ.
        order = Order.objects.create(**validated_data)
        # Создаем элементы заказа.
        for item_data in items_data:
            OrderItem.objects.create(
                order=order,
                item=item_data['item'],
                quantity=item_data['quantity']
            )
        return order

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Добавляем элементы заказа в ответ
        representation['items'] = OrderItemSerializer(
            instance.order_items.all(),
            many=True
        ).data
        return representation
