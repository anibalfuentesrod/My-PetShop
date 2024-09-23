from django.db import models
from django.conf import settings


# Create your models here.
####################################################################################

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveBigIntegerField()
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name # quizas añadir cual es el stock

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