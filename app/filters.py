from email.policy import default
from django import forms
import django_filters
import django_filters.widgets

from app.models import Coupon, FarmerVerification, Product, Order, ProductCategory


class ProductSearchFilter(django_filters.FilterSet):
    """
    Filter for searching products by name or description.
    """
    q = django_filters.CharFilter(field_name='name', lookup_expr='icontains', widget=forms.HiddenInput)
    o = django_filters.OrderingFilter(
        label='Sort by',
        fields=(
            ('price', 'price'),
        ),
    )

    class Meta:
        model = Product
        fields = ['q', 'category', 'type' ]

class OrderFilter(django_filters.FilterSet):
    """
    Filter for searching orders by status and placed_at date range.
    """
    placed_at = django_filters.DateRangeFilter()

    class Meta:
        model = Order
        fields = ['status', 'placed_at']


        