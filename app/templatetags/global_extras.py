from itertools import product
from urllib.parse import unquote
from django import template
from django.urls import reverse
from app.models import ProductCategory

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
    lineitem = request.user.cart().line_items.get(product__id=product_id)
    return lineitem.quantity if lineitem else 0
