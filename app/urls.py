from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from app.views import IndexView, SearchView, CategoryView, SellerStoreView
from app.views import SignupView, LoginView, LogoutView, ProfileView, FarmerVerificationView, OrderListView, OrderDetailView
from app.views import CreateAddressView, UpdateAddressView, DeleteAddressView
from app.views import InventoryListView, CreateProductView, ProductDetailView, UpdateProductView,ListProductImageView, DeleteProductImageView, CreateProductImageView, CreateProductCategoryView
from app.views import AddToCartView,RemoveFromCartView,IncreaseLineItemQuantityView, DecreaseLineItemQuantityView
from app.views import CheckoutView, CheckoutConfirmationView, OrderCompleteView, OrderCancelView
from app.views import CreateReviewView, UpdateReviewView, DeleteReviewView
from app.views import ModeratorView, ModeratorFarmerVerificationView, ModeratorFarmerVerificationStatusUpdateView, ModeratorCategoryView, ModeratorCategoryStatusUpdateView, ModeratorCouponView
from app.views import ModeratorCreateCouponView, ModeratorCouponUpdateView, ModeratorCouponDeleteView
from app.views import FarmerDashboardView

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('search', SearchView.as_view(), name='search'),
    path('category/<str:category>', CategoryView.as_view(), name='category'),
    path('store/<int:pk>', SellerStoreView.as_view(), name='store'),
    # Profile URLs
    path('auth/signup', SignupView.as_view(), name='signup'),
    path('auth/login', LoginView.as_view(), name='login'),
    path('auth/logout', LogoutView.as_view(), name='logout'),
    path('profile', ProfileView.as_view(), name='profile'),
    path('profile/farmer-verification', FarmerVerificationView.as_view(), name='farmer_verification'),
    path('orders', OrderListView.as_view(), name='orders'),
    path('orders/<int:pk>', OrderDetailView.as_view(), name='order_detail'),
    # Address URLs
    path('address/create', CreateAddressView.as_view(), name='create_address'),
    path('address/<int:pk>/update', UpdateAddressView.as_view(), name='update_address'),
    path('address/<int:pk>/delete', DeleteAddressView.as_view(), name='delete_address'),
    # Inventory URLs
    path('inventory', InventoryListView.as_view(), name='inventory'),
    path('product/create', CreateProductView.as_view(), name='create_product'),
    path('product/<int:pk>', ProductDetailView.as_view(), name='product_detail'),
    path('product/<int:pk>/update', UpdateProductView.as_view(), name='update_product'),
    path('product/<int:pk>/images', ListProductImageView.as_view(), name='list_product_images'),
    path('product/<int:pk>/image/<int:image_pk>/delete', DeleteProductImageView.as_view(), name='delete_product_image'),
    path('product/<int:pk>/image', CreateProductImageView.as_view(), name='create_product_image'),
    path('product/<int:pk>/add-to-cart', AddToCartView.as_view(), name='add_to_cart'),
    path('product/<int:pk>/remove-from-cart', RemoveFromCartView.as_view(), name='remove_from_cart'),
    path('product/<int:pk>/increase-quantity', IncreaseLineItemQuantityView.as_view(), name='increase_lineitem_quantity'),
    path('product/<int:pk>/decrease-quantity', DecreaseLineItemQuantityView.as_view(), name='decrease_lineitem_quantity'),
    path('product/category', CreateProductCategoryView.as_view(), name='create_product_category'),
    # Payment URLs
    path('checkout', CheckoutView.as_view(), name='checkout'),
    path('checkout/confirm', CheckoutConfirmationView.as_view(), name='order_confirm'),
    path('order/<int:pk>/complete', OrderCompleteView.as_view(), name='order_complete'),
    path('order/<int:pk>/cancel', OrderCancelView.as_view(), name='order_cancel'),
    # Review URLs
    path('product/<int:pk>/review', CreateReviewView.as_view(), name='create_review'),
    path('product/<int:pk>/review/update', UpdateReviewView.as_view(), name='update_review'),
    path('product/<int:pk>/review/delete', DeleteReviewView.as_view(), name='delete_review'),
    # Moderator URLs
    path('moderator', ModeratorView.as_view(), name='moderator'),
    path('moderator/farmer-verification', ModeratorFarmerVerificationView.as_view(), name='moderator_farmer_verification'),
    path('moderator/farmer-verification/<int:pk>/status', ModeratorFarmerVerificationStatusUpdateView.as_view(), name='moderator_farmer_verification_status_update'),
    path('moderator/category', ModeratorCategoryView.as_view(), name='moderator_category'),
    path('moderator/category/<int:pk>/status', ModeratorCategoryStatusUpdateView.as_view(), name='moderator_category_status_update'),
    path('moderator/coupon', ModeratorCouponView.as_view(), name='moderator_coupon'),
    path('moderator/coupon/create', ModeratorCreateCouponView.as_view(), name="moderator_create_coupon"),
    path('moderator/coupon/<str:pk>/update', ModeratorCouponUpdateView.as_view(), name="moderator_coupon_update"),
    path('moderator/coupon/<str:pk>/delete', ModeratorCouponDeleteView.as_view(), name="moderator_coupon_delete"),
    # Farmer Dashboard
    path('farmer/dashboard', FarmerDashboardView.as_view(), name='farmer_dashboard'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)