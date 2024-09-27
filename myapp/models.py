from django.db import models
from django.conf import settings
import stripe
from django.contrib.auth.models import User
from django.dispatch import receiver
from allauth.account.signals import user_logged_in


# Create your models here.
####################################################################################
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_image = models.URLField(blank=True, null=True)
    google_id = models.CharField(max_length=100, unique=True)
    email = models.EmailField(blank=True, null=True)
    
    def __str__(self) -> str:
        return f"{self.user}, email: {self.email}"


####################################################################################
stripe.api_key = settings.STRIPE_SECRET_KEY

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveBigIntegerField()
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
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
        return f"{self.name} (Stock: {self.stock}, Weight: {self.weight} lbs)"

#####################################################################################

#####################################################################################

class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name # si quieres puedes añadir algo despues


#####################################################################################

#####################################################################################

class Order(models.Model):
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"Order {self.id} by {self.customer.username}"
    
    def calculate_total(self):
        total = sum(item.price * item.quantity for item in self.orderitem_set.all())
        self.total_price = total
        self.save()
#####################################################################################

#####################################################################################

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quiantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self) -> str:
        return f"{self.quiantity} x {self.product.name} in Order {self.order.id}"


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