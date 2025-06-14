from django.contrib import admin

from .models import OrderPayment, ProductReview, User, FarmerVerification, Order, Product, Address, LineItem, Coupon, ProductImage, ProductCategory

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "name", "is_staff", "is_active", "created_at")
    list_filter = ("is_staff","is_active","is_superuser")
    search_fields = ("email__startswith",)
    readonly_fields = ("password",)

    ordering = ("-created_at",)


@admin.register(FarmerVerification)
class FarmerVerificationAdmin(admin.ModelAdmin):
    list_display = ("user", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("user__email__startswith",)
    readonly_fields = ("document",)

    ordering = ("-created_at",)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("__str__", "user", "placed_at", "delivered_at")
    list_filter = ("created_at",)
    search_fields = ("user__email__startswith",)

    ordering = ("-created_at",)

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("name","status", "created_at")
    search_fields = ("name__startswith",)
    list_filter = ("status",)
    ordering = ("-created_at",)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "seller")
    list_filter = ("category",)
    search_fields = ("name__startswith",)

    ordering = ("-created_at",)

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("user", "line1", "city", "state", "country", "created_at")
    search_fields = ("user__email__startswith",)

    ordering = ("-created_at",)

@admin.register(OrderPayment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("__str__", "order", "total_amount", "order__user__name")
    list_filter = ("created_at",)
    search_fields = ("user__email__startswith",)

    ordering = ("-created_at",)

@admin.register(LineItem)
class LineItemAdmin(admin.ModelAdmin):
    list_display = ("pk", "order", "product", "quantity", "price")
    list_filter = ("created_at",)
    search_fields = ("order__user__email__startswith",)

    ordering = ("-created_at",)

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_percentage", "valid_to", "created_at")
    list_filter = ("valid_to",)
    search_fields = ("code__startswith",)

    ordering = ("-created_at",)

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "image", "created_at")
    search_fields = ("product__name__startswith",)

    ordering = ("-created_at",)

@admin.register(ProductReview)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "rating", "created_at")
    list_filter = ("rating",)
    search_fields = ("user__email__startswith",)

    ordering = ("-created_at",)