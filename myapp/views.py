from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, logout
from django.contrib.auth.decorators import login_required
from .models import Order, Product
from django.views import View
import stripe
from django.conf import settings
from django.http import JsonResponse

stripe.api_key = settings.STRIPE_SECRET_KEY
# Create your views here.
############################################################################################
# HOME Page
############################################################################################
def index(request):
    username = request.user
    return render(request, 'index.html', {
        'username': username
    })
############################################################################################
# Registro de Usuario
############################################################################################
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('index')
    else:
        form = UserCreationForm()
    
    return render(request, 'register.html', {
        'form': form
    })

############################################################################################
# Inicio de Sesión
############################################################################################
def login_form(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('profile')
    else:
        form = AuthenticationForm()
    
    return render(request, 'login.html', {
        'form': form
    })
############################################################################################
# Cerrar la Sesión
############################################################################################
def logout_form(request):
    logout(request)
    return redirect('login')
############################################################################################
# Vista Protegida: Dashboard del Usuario
############################################################################################
@login_required
def user_profile(request):
    user = request.user
    return render(request, 'user_profile.html', {
        'username': user.username,
        'email': user.email,
        'date_joined': user.date_joined
    })
############################################################################################
# Todos los productos
############################################################################################
def products(request):
    products = Product.objects.all()
    return render(request, 'products.html', {
        'products': products
    })
############################################################################################
# Los detalles de los productos
############################################################################################
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'product_detail.html', {
        'product': product,
        'STRIPE_PUBLISHABLE_KEY': settings.STRIPE_PUBLISHABLE_KEY,
    })
############################################################################################
# Checkout Session Let's goo
############################################################################################

class CreateCheckoutSessionView(View):
    def post(self, request, *args, **kwargs):
        product_id = self.kwargs['pk']
        product = get_object_or_404(Product, id=product_id)
        
        try:
            checkout_session = stripe.checkout.Session.create(
                line_items=[
                    {
                        'price': product.stripe_price_id,
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url=settings.YOUR_DOMAIN + '/success/',
                cancel_url=settings.YOUR_DOMAIN + '/cancel/',
            )
            return JsonResponse({
                'id': checkout_session.id
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
############################################################################################
# Success Form si el pago fue exitoso
############################################################################################
def success_view(request):
    return render(request, 'success.html')
############################################################################################
# Cancel form si quieres cancelar el pago
############################################################################################
def cancel_view(request):
    return render(request, 'cancel.html')
############################################################################################
# 
############################################################################################