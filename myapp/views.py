from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, logout
from django.contrib.auth.decorators import login_required
from .models import Order, Product
# Create your views here.
############################################################################################
# HOME Page
############################################################################################
def index(request):
    return render(request, 'index.html')
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
@login_required
def product_detail(request, order_id):
    product = get_object_or_404(Order, id=order_id)
    return render(request, 'product_detail.html', {
        'product': product
    })
############################################################################################
#
############################################################################################
