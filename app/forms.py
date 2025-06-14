from email.mime import image
from email.policy import default
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Address, Coupon, Order, OrderPayment, Product, ProductCategory, ProductImage, ProductReview, User, FarmerVerification
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, MultiField, Div
import os
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.core.files.base import ContentFile
from PIL import Image
from io import BytesIO

class UserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email','name')

class FarmerVerificationForm(forms.ModelForm):
    class Meta:
        model = FarmerVerification
        fields = ('document_type', 'document',)

class AddressForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            MultiField(
                '',
                'name',
                Div(
                    'line1',
                    'line2',
                    css_class='grid grid-cols-1 md:grid-cols-2 gap-2'
                ),
                'landmark',
                Div(
                    'city',
                    'pin',
                    css_class='grid grid-cols-1 md:grid-cols-2 gap-2'
                ),
                Div(
                    'state',
                    'country',
                    css_class='grid grid-cols-1 md:grid-cols-2 gap-2'
                ),
            ),
            Submit('submit', 'Save'),
        )

    class Meta:
        model = Address
        fields = ('name', 'line1', 'line2', 'landmark', 'city', 'pin', 'state', 'country',)

class ProductForm(forms.ModelForm):
    category = forms.ModelChoiceField(queryset=ProductCategory.objects.filter(status="Approved"), required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            MultiField(
                '',
                'name',
                'description',
                Div(
                    'category',
                    'type',
                    css_class='grid grid-cols-1 md:grid-cols-2 gap-2'
                ),
                Div(
                    'price',
                    'stock',
                    css_class='grid grid-cols-1 md:grid-cols-2 gap-2'
                ),
                Div(
                    'is_active',
                    'address',
                    css_class='grid grid-cols-1 md:grid-cols-2 gap-2'
                ),
            ),
            Submit('submit', 'Save'),
        )

    class Meta:
        model = Product
        fields = ('name', 'description', 'category', 'type', 'price', 'stock', 'is_active' , 'address')

class ProductImageForm(forms.ModelForm):

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if isinstance(image, InMemoryUploadedFile):
            memory_image = BytesIO(image.read())
            pil_image = Image.open(memory_image)
            pil_image = pil_image.convert('RGB')
            pil_image = pil_image.resize((320, 320), Image.Resampling.BICUBIC)
            new_image = BytesIO()
            pil_image.save(new_image, format='JPEG')
            new_image = ContentFile(new_image.getvalue())
            return InMemoryUploadedFile(new_image, None, image.name, image.content_type, None, None)
        elif isinstance(image, TemporaryUploadedFile):
            path = image.temporary_file_path()
            pil_image = Image.open(path)
            pil_image = pil_image.convert('RGB')
            pil_image = pil_image.resize((320, 320), Image.Resampling.BICUBIC)
            pil_image.save(path)
        return image

    class Meta:
        model = ProductImage
        fields = ('image',)

class OrderCheckoutCombinedForm(forms.Form):
    # Fields from Order model
    address = forms.ModelChoiceField(queryset=Address.objects.none(), required=True)
    is_recurring = forms.BooleanField(required=False, initial=False)
    frequency = forms.ChoiceField(choices=Order.Frequency.choices)

    # Fields from OrderPayment model
    status = forms.ChoiceField(choices=OrderPayment.PaymentStatus.choices)
    payment_method = forms.ChoiceField(choices=OrderPayment.PaymentMethod.choices)
    coupon = forms.CharField(required=False)

    def __init__(self, *args, user=None, **kwargs):
        self.user = user 
        super().__init__(*args, **kwargs)

        if user:
            self.fields['address'].queryset = user.addresses.all()

        self.helper = FormHelper()
        self.helper.layout = Layout(
            MultiField('', 'address', 'is_recurring', 'frequency', 'status', 'payment_method', 'coupon'),
            Submit('submit', 'Validate and Pay'),
        )

    def clean_coupon(self):
        code = self.cleaned_data.get('coupon')
        if code:
            try:
                return Coupon.objects.get(code=code)
            except Coupon.DoesNotExist:
                raise forms.ValidationError("Invalid coupon code.")
        return None
    
    def is_valid(self):
        is_valid = super().is_valid()
        if not is_valid:
            return is_valid
        status = self.cleaned_data.get('status')
        payment_method = self.cleaned_data.get('payment_method')
        coupon = self.cleaned_data.get('coupon')
        if status == OrderPayment.PaymentStatus.PENDING and payment_method == OrderPayment.PaymentMethod.CASH:
            return is_valid
        if status == OrderPayment.PaymentStatus.FAILED or (status == OrderPayment.PaymentStatus.PENDING and payment_method != OrderPayment.PaymentMethod.CASH):
            self.add_error('status', "Payment failed. Please try again.")
            order = self.user.cart()
            order_payment = OrderPayment(
                order=order,
                status=status,
                payment_method=payment_method,
                coupon=coupon
            )
            order_payment.process_payment()
            return False
        return is_valid

    def save(self):
        """Custom save method to create both Order and OrderPayment"""
        order = self.user.cart()
        address = self.cleaned_data['address']
        order.recipient_name = address.name
        order.delivery_address = address.full_address()
        order.is_recurring = self.cleaned_data['is_recurring']
        order.frequency = self.cleaned_data['frequency']
        order.save()
        order_payment = OrderPayment(
            order=order,
            status=self.cleaned_data['status'],
            payment_method=self.cleaned_data['payment_method'],
            coupon=self.cleaned_data.get('coupon'),
            rain_surcharge=True
        )
        order_payment.process_payment()

class OrderConfirmForm(forms.Form):
    status = forms.ChoiceField(choices=(('Yes', 'Yes'), ('No', 'No')), required=True, label="Confirm Order")

    def __init__(self, *args, user=None, **kwargs):
        self.user = user 
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            MultiField(
                '',
                'status',
            ),
            Submit('submit', 'Confirm Order'),
        )

    def save(self):
        """Custom save method to confirm the order"""
        order = self.user.cart()
        if self.cleaned_data['status'] == 'No':
            if order.payments.exists():
                order_payment = order.payments.last()
                order_payment.status = OrderPayment.PaymentStatus.FAILED
                order_payment.save()
        else:
            order.purchase()

class ProductReviewForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            MultiField(
                '',
                'review',
                'rating',
                'image',
            ),
            Submit('submit', 'Submit'),
        )

    class Meta:
        model = ProductReview
        fields = ('review','rating','image')
        

