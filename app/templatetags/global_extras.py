from itertools import product
from urllib.parse import unquote
from django import template
from django.urls import reverse
from app.models import Order, ProductCategory

register = template.Library()

@register.simple_tag
def get_breadcrumb_categories():
    return ProductCategory.objects.filter(status=ProductCategory.ApprovalStatus.APPROVED).order_by('name')

@register.filter
def in_lineitems(lineitems, product):
    return lineitems.get(product=product)

@register.simple_tag(takes_context=True)
def is_url_active(context, url_to_check: str, *args, **kwargs) -> str:
    request = context['request']
    if request.path == unquote(reverse(url_to_check, args=args, kwargs=kwargs)):
        return 'active'
    return 'anti-active'

@register.simple_tag(takes_context=True)
def get_lineitem_quantity_from_cart(context, product_id: int):
    request = context['request']
    lineitem = request.user.orders.filter(status=Order.OrderStatus.CART).first().line_items.get(product__id=product_id)
    return lineitem.quantity if lineitem else 0

@register.filter
def aggregate(items, field):
    sum = 0
    for item in items:
        if hasattr(item, field):
            value = getattr(item, field)
            if callable(value):
                sum += value()
            else:
                sum += value
    return sum


@register.simple_tag
def refine(queryset, field, value):
    """
    Filters the queryset based on the field and value provided.
    """
    if not hasattr(queryset, 'filter'):
        raise ValueError("The provided queryset does not support filtering.")
    
    filter_kwargs = {field: value}
    return queryset.filter(**filter_kwargs)

@register.simple_tag
def pick(queryset, field, value):
    """
    Returns the first item in the queryset that matches the field and value.
    """
    if not hasattr(queryset, 'filter'):
        raise ValueError("The provided queryset does not support filtering.")
    
    return next((item for item in queryset.all() if getattr(item,field) == value), None)

@register.simple_tag
def pluck(queryset, field_name):
    """
    Returns a list of values for the specified field from the queryset.
    """
    return [getattr(item, field_name) for item in queryset if hasattr(item, field_name)]

@register.simple_tag
def prefetch_related(queryset, *fields):
    """
    Prefetches related fields for the queryset.
    """
    if not hasattr(queryset, 'prefetch_related'):
        raise ValueError("The provided queryset does not support prefetching.")
    
    return queryset.prefetch_related(*fields)