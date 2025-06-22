from urllib.parse import unquote
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db.models import Sum
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import uuid

from app.managers import UserManager

def upload_product_image(instance,filename):
    return "products/"+uuid.uuid4().hex+"."+filename.split(".")[-1]

def upload_review_image(instance,filename):
    return "reviews/"+uuid.uuid4().hex+"."+filename.split(".")[-1]

def upload_verification_document(instance,filename):
    return "verification/"+uuid.uuid4().hex+"."+filename.split(".")[-1]

def generate_order_reference():
    return str(uuid.uuid4())

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_("Email Address"),unique=True,max_length=127)
    name = models.CharField(_("Name"),max_length=255)
    
    
    is_farmer = models.BooleanField(default=False)
    is_moderator = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ["name"]
    
    def reviewed_products(self):
        return Product.objects.filter(reviews__user=self)
    
    def rating_distribution(self):
        total = self.products.aggregate(total=models.Count('reviews'))['total'] or 0
        if total == 0:
            return {i: 0 for i in range(1, 6)}
        distribution = self.products.values('reviews__rating').annotate(count=models.Count('reviews__rating')).values('reviews__rating', 'count')
        return {item['reviews__rating']: int(item['count'] * 100 / total) for item in distribution}
    
    def __str__(self):
        return self.name
    
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField(_("Notification Message"))
    link_to = models.URLField(_("Link to"), blank=True, null=True)

    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)


class FarmerVerification(models.Model):
    class DocumentType(models.TextChoices):
        AADHAR = "Aadhar", _("Aadhar")
        PAN = "PAN", _("PAN")
        GST = "GST", _("GST")
        OTHER = "Other", _("Other")

    class VerificationStatus(models.TextChoices):
        PENDING = "Pending", _("Pending")
        APPROVED = "Approved", _("Approved")
        REJECTED = "Rejected", _("Rejected")

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="verifications")
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="verified_by_me")
    document_type = models.CharField(_("Document Type"), max_length=20, choices=DocumentType.choices, default=DocumentType.AADHAR)
    document = models.FileField(_("Verification Document"), upload_to=upload_verification_document)
    status = models.CharField(_("Verification Status"), max_length=20, choices=VerificationStatus.choices, default=VerificationStatus.PENDING)

    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    def __str__(self):
        return f"{self.user.name} - {self.status}"
    
class Address(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name="addresses")
    name = models.CharField(_("Full Name"), max_length=255)
    line1 = models.CharField(_("Address Line 1"), max_length=127)
    line2 = models.CharField(_("Address Line 2"), max_length=127, blank=True, null=True)
    landmark = models.CharField(_("Nearest Landmark"), max_length=127, blank=True, null=True)
    city = models.CharField(_("City"), max_length=127)
    pin = models.CharField(_("Pin Code"), max_length=127)
    state = models.CharField(_("State"), max_length=127)
    country = models.CharField(_("Country"), max_length=127)

    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.line1}, {self.city} {self.pin}, {self.state}, {self.country}"
    
    def full_address(self):
        return f"{self.line1}, {self.line2 or ''}, {self.landmark or ''}, {self.city}, {self.pin}, {self.state}, {self.country}".strip(", ")
    
class ProductCategory(models.Model):
    class ApprovalStatus(models.TextChoices):
        PENDING = "Pending", _("Pending")
        APPROVED = "Approved", _("Approved")
        REJECTED = "Rejected", _("Rejected")

    name = models.CharField(_("Category Name"), max_length=255)
    description = models.TextField(_("Category Description"))
    status = models.CharField(_("Approval Status"), max_length=20, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING)

    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    def get_absolute_url(self):
        return unquote(reverse("category", kwargs={"category": self.name}))
    
    def __str__(self):
        return self.name

class Product(models.Model):
    class ProductType(models.TextChoices):
        FRESH = "Fresh", _("Fresh (Consume within 2 hours)")
        COLD = "Cold", _("Cold (Consume within 24 hours)")
        AMBIENT = "Ambient", _("Ambient (Consume within 7 days)")
        FROZEN = "Frozen", _("Frozen (Consume within 30 days)")
        DRIED = "Dried", _("Dried (Consume within 90 days)")
        PROCESSED = "Processed", _("Processed (Consume within 180 days)")
        PACKAGED = "Packaged", _("Packaged (Consume within 365 days)")


    name = models.CharField(_("Product Name"), max_length=255)
    description = models.TextField(_("Product Description"))
    address = models.ForeignKey(Address, on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, related_name="products")
    type = models.CharField(_("Product Type"), max_length=20, choices=ProductType.choices, default=ProductType.FRESH)
    price = models.DecimalField(_("Product Price"), max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(_("Product Stock"))
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="products")
    is_active = models.BooleanField(_("Is Active"), default=True)

    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    def __str__(self):
        return self.name
    
    def rating(self):
        if not self.reviews.exists():
            return 0
        total_rating = sum(review.rating for review in self.reviews.all())
        return total_rating / self.reviews.count()
    
    def cart_count(self):
        return self.line_items.filter(order__status=Order.OrderStatus.CART).aggregate(Sum('quantity'))['quantity__sum'] or 0
    
    def rating_distribution(self):
        total = self.reviews.count()
        if total == 0:
            return {i: 0 for i in range(1, 6)}
        distribution = self.reviews.values('rating').annotate(count=models.Count('rating'))
        return { item['rating']: int(item['count']*100/total) for item in distribution }
    
    def in_stock(self):
        return self.stock > 0

class ProductImage(models.Model):
    product = models.ForeignKey(Product,on_delete=models.CASCADE,related_name="images")
    image = models.ImageField(_("Product Image"), upload_to=upload_product_image)

    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    def __str__(self):
        return f"{self.product.name} - Image ID: {self.id}"

class Order(models.Model):
    class OrderStatus(models.TextChoices):
        CART = "Cart", _("Cart")
        PENDING = "Pending", _("Pending")
        DELIVERED = "Delivered", _("Delivered")
        CANCELLED = "Cancelled", _("Cancelled")
    
    class Frequency(models.TextChoices):
        NONE = "None", _("None")
        DAILY = "Daily", _("Daily")
        WEEKLY = "Weekly", _("Weekly")
        MONTHLY = "Monthly", _("Monthly")

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    reference = models.CharField(_("Order Reference"), max_length=255, default=generate_order_reference)
    recipient_name = models.CharField(_("Recipient Name"), max_length=255, blank=True, null=True)
    delivery_address = models.CharField(_("Delivery Address"), max_length=511, blank=True, null=True)
    status = models.CharField(_("Order Status"), max_length=20, choices=OrderStatus.choices, default=OrderStatus.CART)
    
    is_recurring = models.BooleanField(_("Is Recurring"), default=False)
    frequency = models.CharField(_("Frequency"), max_length=20, choices=Frequency.choices, default=Frequency.NONE)
    next_delivery_date = models.DateField(_("Next Delivery Date"), null=True, blank=True)

    placed_at = models.DateTimeField(_("Order Placed"), blank=True, null=True)
    delivered_at = models.DateTimeField(_("Order Delivered"), blank=True, null=True)

    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def platform_fee(self) -> float:
        return self.total_price() * 0.01
    
    def total_price(self) -> float:
        return float(sum([item.total_price() for item in self.line_items.all() ]))
    
    def purchase(self):
        if self.status != Order.OrderStatus.CART:
            raise ValidationError(_("Order is not in cart status"), code="invalid_order_status")
        for line_item in self.line_items.all():
            line_item.purchase()
        self.status = Order.OrderStatus.PENDING
        self.placed_at = timezone.now()
        if self.is_recurring:
            if self.frequency == Order.Frequency.DAILY:
                self.next_delivery_date = timezone.now() + timezone.timedelta(days=1)
            elif self.frequency == Order.Frequency.WEEKLY:
                self.next_delivery_date = timezone.now() + timezone.timedelta(weeks=1)
            elif self.frequency == Order.Frequency.MONTHLY:
                self.next_delivery_date = timezone.now() + timezone.timedelta(weeks=4)
        self.save()

    def deliver(self):
        if self.status != Order.OrderStatus.PENDING:
            raise ValidationError(_("Order cannot be delivered"), code="invalid_order_status")
        self.status = Order.OrderStatus.DELIVERED
        self.delivered_at = timezone.now()
        self.save()
        if self.is_recurring:
            self.place_next_order()

    def stop_recurring(self):
        self.is_recurring = False
        self.frequency = Order.Frequency.NONE
        self.next_delivery_date = None
        self.save()
        Order.objects.filter(user=self.user, status=Order.OrderStatus.PENDING, reference=self.reference, placed_at__gt=timezone.now()).delete()

    def place_next_order(self):
        order = Order.objects.create(
            user=self.user,
            reference=self.reference,
            recipient_name=self.recipient_name,
            delivery_address=self.delivery_address,
            status=Order.OrderStatus.PENDING,
            is_recurring=self.is_recurring,
            frequency=self.frequency,
            placed_at=self.next_delivery_date
        )
        line_items = self.line_items.all()
        for line_item in line_items:
            LineItem.objects.create(
                order=order,
                product=line_item.product,
                quantity=line_item.quantity,
                price=line_item.price
            )
        return order

    def cancel(self):
        if self.status != Order.OrderStatus.PENDING:
            raise ValidationError(_("Order cannot be cancelled"), code="invalid_order_status")
        self.status = Order.OrderStatus.CANCELLED
        self.save()
        if self.is_recurring:
            self.stop_recurring()

    def __str__(self):
        return f"Order {self.reference}"
    
    class Meta:
        ordering = ['-created_at']

class LineItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="line_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="line_items")
    quantity = models.PositiveIntegerField(_("Quantity"))
    price = models.DecimalField(_("Price"), max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    def in_stock(self):
        return self.product.stock >= self.quantity
    
    def total_price(self):
        return self.product.price * self.quantity
    
    def increase_quantity(self, amount=1):
        if self.product.stock < self.quantity + amount:
            raise ValidationError(_("Not enough stock available"), code="not_enough_stock")
        self.quantity += amount
        self.save()

    def decrease_quantity(self, amount=1):
        if self.quantity - amount < 1:
            raise ValidationError(_("Quantity cannot be less than 1"), code="invalid_quantity")
        self.quantity -= amount
        self.save()

    def purchase(self):
        if not self.in_stock():
            raise ValidationError(_("Product out of stock"), code="out_of_stock")
        self.product.stock -= self.quantity
        self.product.save()
        self.price = self.product.price
        self.save()

    def __str__(self):
        return f"{self.product.name} - {self.quantity} pcs"

class Coupon(models.Model):
    code = models.CharField(_("Coupon Code"), max_length=20, unique=True, primary_key=True)
    discount_percentage = models.DecimalField(_("Discount Percentage"), max_digits=5, decimal_places=2)
    max_discount = models.DecimalField(_("Maximum Discount"), max_digits=10, decimal_places=2)
    min_order_value = models.DecimalField(_("Minimum Order Value"), max_digits=10, decimal_places=2)
    valid_from = models.DateTimeField(_("Valid From"))
    valid_to = models.DateTimeField(_("Valid To"))

    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    def is_active(self):
        return self.valid_from <= timezone.now() <= self.valid_to
    
    def redacted_code(self):
        redact_length = int(len(self.code) / 2)
        return self.code[:redact_length] + "****"

    def __str__(self):
        return self.code

class OrderPayment(models.Model):
    class PaymentStatus(models.TextChoices):
        PENDING = "Pending", _("Pending")
        COMPLETED = "Completed", _("Completed")
        FAILED = "Failed", _("Failed")

    class PaymentMethod(models.TextChoices):
        CREDIT_CARD = "Credit Card", _("Credit Card")
        DEBIT_CARD = "Debit Card", _("Debit Card")
        NET_BANKING = "Net Banking", _("Net Banking")
        UPI = "UPI", _("UPI")
        CASH = "Cash", _("Cash")

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    order_amount = models.DecimalField(_("Payment Amount"), max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(_("Discount"), max_digits=10, decimal_places=2, default=0.0)
    delivery_charge = models.DecimalField(_("Delivery Charge"), max_digits=10, decimal_places=2, default=30.0)
    rain_surcharge = models.BooleanField(_("Rain Surcharge"), default=False, help_text=_("Whether rain surcharge is applicable for this order"))

    status = models.CharField(_("Payment Status"), max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    payment_method = models.CharField(_("Payment Method"), max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.CREDIT_CARD)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments")

    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    def __str__(self):
        return f"Payment #{self.pk} - {self.status}"

    def process_payment(self):
        self.order_amount = self.order.total_price()
        if self.coupon and self.coupon.is_active():
            discount = float(self.coupon.discount_percentage / 100) * self.order.total_price()
            if discount > self.coupon.max_discount:
                discount = self.coupon.max_discount
            self.discount_amount = discount
        if self.coupon and self.coupon.is_active() and self.order.total_price() < self.coupon.min_order_value:
            raise ValidationError(_("Order value is less than minimum order value for this coupon"), code="invalid_order_value")
        if self.rain_surcharge:
            self.delivery_charge += 20.0
        self.save()

    def total_amount(self):
        return self.order_amount + self.delivery_charge - self.discount_amount
    
    class Meta:
        ordering = ['-created_at']
        
class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    review = models.TextField(_("Review"))
    rating = models.IntegerField(_("Rating"), choices=[(i, str(i)) for i in range(1, 6)]) 
    image = models.ImageField(_("Review Image"), upload_to=upload_review_image, blank=True, null=True)

    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        unique_together = ('product', 'user',)
        ordering = ['-created_at']
    