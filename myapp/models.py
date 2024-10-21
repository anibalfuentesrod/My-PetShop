from django.db import models
from django.conf import settings
import stripe
from django.contrib.auth.models import User
from django.dispatch import receiver
from allauth.account.signals import user_logged_in
from django.core.exceptions import ValidationError


# Create your models here.
####################################################################################
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_image = models.URLField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    
    def __str__(self) -> str:
        return f"{self.user}, email: {self.email}"


####################################################################################
stripe.api_key = settings.STRIPE_SECRET_KEY

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available = models.BooleanField(default=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    stripe_price_id = models.CharField(max_length=255, null=True, blank=True)
    
    def save(self, *args, **kwargs):
        # solo crear en stripe si no tiene un 'stripe_id'
        if not self.stripe_price_id:
            stripe_product = stripe.Product.create(
                name=self.name,
                description=self.description,
            )
            stripe_price = stripe.Price.create(
                product=stripe_product.id,
                unit_amount=int(self.price * 100),
                currency='usd',
            )
            self.stripe_price_id = stripe_price.id
        super().save(*args, **kwargs)
    
    def __str__(self) -> str:
        return f"{self.name} (Available: {self.available}, Weight: {self.weight} lbs)"

#####################################################################################


#####################################################################################

class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name # si quieres puedes añadir algo despues


#####################################################################################

class ShippingAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    direccion = models.CharField(max_length=255)
    ciudad = models.CharField(max_length=100)
    estado = models.CharField(max_length=100)
    codigo_postal = models.CharField(max_length=20)
    country = models.CharField(max_length=100)  # No default value
    
    def clean(self):
        allowed_countries = ['US', 'PR', 'CA']  # List of allowed countries
        if self.country not in allowed_countries:
            raise ValidationError(f"Shipping to {self.country} is not supported.")
#####################################################################################

class Order(models.Model):
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Order '{self.id}' by '{self.customer.username}', fecha: {self.created_at}"
#####################################################################################

#####################################################################################

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self) -> str:
        return f"'{self.quantity}' x {self.product.name} in Order id: '{self.order.id}'"


#####################################################################################

#####################################################################################

class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    stripe_charge_id = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default='pending')

    def __str__(self) -> str:
        return f"Payment {self.id} for Order {self.order.id}"

#####################################################################################

class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Cart of {self.user.username}"

    def total_items(self):
        return sum(item.quantity for item in self.cartitem_set.all())
    
    def total_price(self):
        return sum(item.product.price * item.quantity for item in self.cartitem_set.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)


    def __str__(self) -> str:
        return f"{self.quantity} of {self.product.name} in {self.cart.user.username}'s cart"