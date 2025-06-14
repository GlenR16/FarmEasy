import time
from django.forms import formset_factory
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView
from django.views.generic import FormView, CreateView, UpdateView, DeleteView, DetailView, ListView
from django_filters.views import FilterView
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.views import PasswordChangeView
from django.views.generic import RedirectView

from app.filters import OrderFilter, ProductSearchFilter
from app.models import Address, Coupon, FarmerVerification, Order, OrderPayment, Product, ProductImage, ProductReview, ProductCategory
from app.forms import AddressForm, FarmerVerificationForm, OrderCheckoutCombinedForm, OrderConfirmForm, ProductForm, ProductImageForm, ProductReviewForm, UserCreationForm

class IndexView(TemplateView):
    template_name = 'index.html'

class SignupView(UserPassesTestMixin,FormView):
    template_name = "auth/signup.html"
    form_class = UserCreationForm

    def form_valid(self, form):
        user = form.save()
        Order.objects.create(user=user)
        login(self.request, user)
        return super().form_valid(form)
    
    def test_func(self):
        return not self.request.user.is_authenticated
    
    def get_success_url(self) -> str:
        return self.request.GET.get("next", "/")
    
class LoginView(UserPassesTestMixin,FormView):
    template_name = "auth/login.html"
    form_class = AuthenticationForm

    def form_valid(self, form):
        user = authenticate(self.request, email=form.cleaned_data["username"], password=form.cleaned_data["password"])
        if user is not None:
            login(self.request, user)
            return super().form_valid(form)
        return self.form_invalid(form)
        
    def test_func(self):
        return not self.request.user.is_authenticated
    
    def get_success_url(self) -> str:
        return self.request.GET.get("next", "/")

class LogoutView(LoginRequiredMixin,RedirectView):
    url = '/'

    def get(self, request, *args, **kwargs):
        logout(request)
        return super().get(request, *args, **kwargs)
    
class SearchView(FilterView):
    template_name = 'search.html'
    filterset_class = ProductSearchFilter
    
class ProfileView(LoginRequiredMixin,PasswordChangeView):
    template_name = 'profile.html'
    form_class = PasswordChangeForm
    success_url = '/profile'
    
class FarmerVerificationView(LoginRequiredMixin, UserPassesTestMixin,FormView):
    form_class = FarmerVerificationForm
    template_name = 'farmer_verification.html'
    success_url = '/profile'

    def form_valid(self, form):
        if FarmerVerification.objects.filter(
                user=self.request.user,
                status=FarmerVerification.VerificationStatus.PENDING
            ).exists():
            form.add_error('document', 'You already have a pending verification request.')
            return self.form_invalid(form)
        verification = form.save(commit=False)
        verification.user = self.request.user
        verification.save()
        return super().form_valid(form)
    
    def test_func(self):
        return not self.request.user.is_farmer

class CreateAddressView(LoginRequiredMixin, FormView):
    form_class = AddressForm
    template_name = 'address/create_address.html'
    success_url = '/profile'
    
    def form_valid(self, form):
        address = form.save(commit=False)
        address.user = self.request.user
        address.save()
        return super().form_valid(form)

class UpdateAddressView(LoginRequiredMixin, UpdateView):
    form_class = AddressForm
    template_name = 'address/update_address.html'
    success_url = '/profile'

    def get_queryset(self):
        return self.request.user.addresses.all()
    
class DeleteAddressView(LoginRequiredMixin, DeleteView):
    model = Address
    template_name = 'address/delete_address.html'
    success_url = '/profile'

    def get_queryset(self):
        return self.request.user.addresses.all()

class OrderListView(LoginRequiredMixin, FilterView):
    model = Order
    template_name = 'order/list_order.html'
    filterset_class = OrderFilter

    def get_queryset(self):
        return self.request.user.orders.exclude(status=Order.OrderStatus.CART).exclude(placed_at__gte=timezone.now()).order_by('-created_at')
    
class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'order/view_order.html'
    context_object_name = 'order'

    def get_queryset(self):
        return self.request.user.orders.exclude(status=Order.OrderStatus.CART)
    
class InventoryListView(LoginRequiredMixin, FilterView):
    model = Product
    template_name = 'inventory/list_inventory.html'
    filterset_fields = ['category', 'created_at']

    def get_queryset(self):
        return self.request.user.products.all()
    
class CreateProductView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    form_class = ProductForm
    template_name = 'product/create_product.html'
    success_url = '/inventory'

    def form_valid(self, form):
        product = form.save(commit=False)
        product.seller = self.request.user
        product.save()
        return super().form_valid(form)
    
    def test_func(self):
        return self.request.user.is_farmer
    
class ProductDetailView(DetailView):
    model = Product
    template_name = 'product/view_product.html'

    def get_queryset(self):
        return Product.objects.all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['review_form'] = ProductReviewForm()
        return context

class UpdateProductView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    form_class = ProductForm
    template_name = 'product/update_product.html'
    success_url = '/inventory'

    def get_queryset(self):
        return self.request.user.products.all()
    
    def test_func(self):
        return self.request.user.is_farmer

class ListProductImageView(LoginRequiredMixin, ListView):
    model = ProductImage
    template_name = 'product_image/list_product_image.html'

    def get_queryset(self):
        return self.request.user.products.get(pk=self.kwargs['pk']).images.all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product_id'] = self.kwargs['pk']
        return context

class DeleteProductImageView(LoginRequiredMixin, DeleteView):
    model = ProductImage
    template_name = 'product_image/delete_product_image.html'

    def get_object(self, queryset=None):
        return self.request.user.products.get(pk=self.kwargs['pk']).images.get(pk=self.kwargs['image_pk'])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product_id'] = self.kwargs['pk']
        return context
    
    def get_success_url(self):
        return reverse('list_product_images', kwargs={'pk': self.kwargs['pk']})
    
class CreateProductImageView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = 'product_image/create_product_image.html'
    success_url = '/inventory'

    def get_form_class(self):
        return formset_factory(ProductImageForm, extra=int(self.request.GET.get('extra', 1)), max_num=6)
    
    def form_valid(self, form):
        product = self.request.user.products.get(pk=self.kwargs['pk'])
        for form in form:
            if form.is_valid():
                product_image = form.save(commit=False)
                product_image.product = product
                product_image.save()
        return super().form_valid(form)
    
    def test_func(self):
        return self.request.user.is_farmer


class AddToCartView(LoginRequiredMixin , RedirectView):
    
    def get_redirect_url(self, *args, **kwargs):
        return self.request.GET.get("next", "/")

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.filter(pk=self.kwargs['pk']).exists():
            return super().get(request, *args, **kwargs)
        product = queryset.get(pk=self.kwargs['pk'])
        if not product.in_stock():
            return super().get(request, *args, **kwargs)
        order = self.request.user.cart()
        if not order:
            order = Order.objects.create(user=self.request.user, status=Order.OrderStatus.CART)
        order.line_items.create(product=product, quantity=1, price=product.price)
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        return Product.objects.exclude(seller=self.request.user, is_active=False)
    
class RemoveFromCartView(LoginRequiredMixin , RedirectView):
    
    def get_redirect_url(self, *args, **kwargs):
        return self.request.GET.get("next", "/")

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.filter(pk=self.kwargs['pk']).exists():
            return super().get(request, *args, **kwargs)
        product = queryset.get(pk=self.kwargs['pk'])
        order = self.request.user.cart()
        order.line_items.filter(product=product).delete()
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        return Product.objects.exclude(seller=self.request.user)

class IncreaseLineItemQuantityView(LoginRequiredMixin , RedirectView):
    
    def get_redirect_url(self, *args, **kwargs):
        return self.request.GET.get("next", "/")

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.filter(pk=self.kwargs['pk']).exists():
            return super().get(request, *args, **kwargs)
        product = queryset.get(pk=self.kwargs['pk'])
        order = self.request.user.cart()
        lineitem = order.line_items.get(product=product)
        lineitem.increase_quantity()
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        return Product.objects.exclude(seller=self.request.user)
    
class DecreaseLineItemQuantityView(LoginRequiredMixin , RedirectView):
    
    def get_redirect_url(self, *args, **kwargs):
        return self.request.GET.get("next", "/")

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.filter(pk=self.kwargs['pk']).exists():
            return super().get(request, *args, **kwargs)
        product = queryset.get(pk=self.kwargs['pk'])
        order = self.request.user.cart()
        lineitem = order.line_items.get(product=product)
        lineitem.decrease_quantity()
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        return Product.objects.exclude(seller=self.request.user)
    
class OrderCompleteView(LoginRequiredMixin, UserPassesTestMixin, RedirectView):
    url = '/farmer/dashboard'

    def test_func(self):
        return self.request.user.is_farmer
    
    def get(self, request, *args, **kwargs):
        order = Order.objects.get(pk=self.kwargs['pk'], status=Order.OrderStatus.PENDING)
        if order and order.line_items.exists():
            my_products = request.user.products.filter(pk__in=order.line_items.values_list('product', flat=True))
            if my_products.exists():
                order.deliver()
        return super().get(request, *args, **kwargs)

class OrderCancelView(LoginRequiredMixin, UserPassesTestMixin, RedirectView):
    url = '/farmer/dashboard'

    def test_func(self):
        return self.request.user.is_farmer
    
    def get(self, request, *args, **kwargs):
        order = Order.objects.get(pk=self.kwargs['pk'], status=Order.OrderStatus.PENDING)
        if order and order.line_items.exists():
            my_products = request.user.products.filter(pk__in=order.line_items.values_list('product', flat=True))
            if my_products.exists():
                order.cancel()
        return super().get(request, *args, **kwargs)

class CheckoutView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = 'checkout.html'
    form_class = OrderCheckoutCombinedForm
    success_url = '/checkout/confirm'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def test_func(self):
        return self.request.user.cart() and self.request.user.cart().line_items.exists() 
    
    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

class CheckoutConfirmationView(LoginRequiredMixin,UserPassesTestMixin, FormView):
    template_name = 'checkout_confirmation.html'
    form_class = OrderConfirmForm
    success_url = '/orders'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def test_func(self):
        cart = self.request.user.cart()
        if cart and (OrderPayment.objects.filter(order=cart, status=OrderPayment.PaymentStatus.PENDING, payment_method=OrderPayment.PaymentMethod.CASH).exists() or OrderPayment.objects.filter(order=cart, status=OrderPayment.PaymentStatus.COMPLETED).exists()):
            return True
        return False
    
    def form_valid(self, form):
        form.save()
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class CategoryView(TemplateView):
    template_name = 'category.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = Product.objects.filter(category__name=self.kwargs['category'], is_active=True)
        return context

class CreateReviewView(LoginRequiredMixin, CreateView):
    form_class = ProductReviewForm
    template_name = 'review/create_review.html'
    
    def get_success_url(self):
        return f"/product/{self.kwargs['pk']}"

    def form_valid(self, form):
        review = form.save(commit=False)
        review.user = self.request.user
        review.product = Product.objects.get(pk=self.kwargs['pk'])
        review.save()
        return super().form_valid(form)
    
class UpdateReviewView(LoginRequiredMixin, UpdateView):
    form_class = ProductReviewForm
    template_name = 'review/update_review.html'
    
    def get_success_url(self):
        return f"/product/{self.kwargs['pk']}"
    
    def get_queryset(self):
        return self.request.user.reviews.all()

class DeleteReviewView(LoginRequiredMixin, DeleteView):
    model = ProductReview
    template_name = 'review/delete_review.html'
    
    def get_success_url(self):
        return f"/product/{self.kwargs['pk']}"
    
    def get_queryset(self):
        return self.request.user.reviews.all()
    
class CreateProductCategoryView(LoginRequiredMixin, CreateView):
    model = ProductCategory
    fields = ['name', 'description']
    template_name = 'product_category/create_product_category.html'
    success_url = '/'

class SellerStoreView(LoginRequiredMixin, TemplateView):
    template_name = 'seller_store.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = Product.objects.filter(seller=self.kwargs['pk'])
        return context
    
class ModeratorView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'moderator/moderator.html'
    
    def test_func(self):
        return self.request.user.is_moderator
    
class ModeratorFarmerVerificationView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = FarmerVerification
    template_name = 'moderator/farmer_verification.html'
    
    def test_func(self):
        return self.request.user.is_moderator
    
    def get_queryset(self):
        return FarmerVerification.objects.filter(status=FarmerVerification.VerificationStatus.PENDING)

class ModeratorFarmerVerificationStatusUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = FarmerVerification
    fields = ['status']
    template_name = 'moderator/farmer_verification_status_update.html'
    
    def test_func(self):
        return self.request.user.is_moderator
    
    def get_success_url(self):
        return '/moderator/farmer-verification'
    
    def get_queryset(self):
        return FarmerVerification.objects.filter(status=FarmerVerification.VerificationStatus.PENDING)  
    
    def form_valid(self, form):
        form.save(commit=False)
        form.instance.verified_by = self.request.user
        form.instance.save()
        if form.instance.status == FarmerVerification.VerificationStatus.APPROVED:
            form.instance.user.is_farmer = True
            form.instance.user.save()
        return super().form_valid(form)
    
    
class ModeratorCategoryView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = ProductCategory
    template_name = 'moderator/category.html'
    
    def test_func(self):
        return self.request.user.is_moderator
    
    def get_queryset(self):
        return ProductCategory.objects.filter(status=ProductCategory.ApprovalStatus.PENDING)

class ModeratorCategoryStatusUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ProductCategory
    fields = ['status']
    template_name = 'moderator/category_status_update.html'
    
    def test_func(self):
        return self.request.user.is_moderator
    
    def get_success_url(self):
        return '/moderator/category'
    
    def get_queryset(self):
        return ProductCategory.objects.filter(status=ProductCategory.ApprovalStatus.PENDING)   

class ModeratorCouponView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Coupon
    template_name = 'moderator/coupon.html'
    
    def test_func(self):
        return self.request.user.is_moderator
    
    def get_queryset(self):
        return Coupon.objects.all().order_by('-created_at')

class ModeratorCreateCouponView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Coupon
    fields = ["code", "discount_percentage", "max_discount", "min_order_value", "valid_from", "valid_to"]
    template_name = "moderator/create_coupon.html"
    success_url = '/moderator/coupon'

    def test_func(self):
        return self.request.user.is_moderator
    
class ModeratorCouponUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Coupon
    fields = ['discount_percentage', 'max_discount', 'min_order_value', 'valid_from', 'valid_to']
    template_name = 'moderator/update_coupon.html'
    success_url = '/moderator/coupon'

    def test_func(self):
        return self.request.user.is_moderator
    
class ModeratorCouponDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Coupon
    template_name = 'moderator/delete_coupon.html'
    success_url = '/moderator/coupon'

    def test_func(self):
        return self.request.user.is_moderator
    
    def get_queryset(self):
        return Coupon.objects.all()
    
class FarmerDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'farmer_dashboard.html'
    
    def test_func(self):
        return self.request.user.is_farmer
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pending_deliveries'] = Order.objects.filter(status=Order.OrderStatus.PENDING, line_items__product__seller=self.request.user,placed_at__lte=timezone.now()).distinct()
        return context