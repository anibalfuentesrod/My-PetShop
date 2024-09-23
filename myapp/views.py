from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, logout
from django.contrib.auth.decorators import login_required
from .models import Order
# Create your views here.
############################################################################################
# HOME
############################################################################################
def home(request):
    return render(request, 'home.html')
############################################################################################
# Registro de Usuario
############################################################################################
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    
    return render(request, 'register.html', {
        'form': form
    })

############################################################################################
# Inicio de Sesión
############################################################################################
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    
    return render(request, 'login.html', {
        'form': form
    })
############################################################################################
# Cerrar la Sesión
############################################################################################
def logout_view(request):
    logout(request)
    return redirect('login')
############################################################################################
# Vista Protegida: Dashboard del Usuario
############################################################################################
@login_required
def user_dashboard(request):
    return render(request, 'dashboard.html')
############################################################################################
# Detalle de Pedido
############################################################################################
@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    return render(request, 'order_detail.html', {
        'order': order
    })
############################################################################################
# Listea tus Order si no tienes ps te da un mensaje
############################################################################################
@login_required
def order_list(request):
    orders = Order.objects.filter(customer=request.user)
    return render(request, 'order_list.html', {
        'orders': orders
    })
############################################################################################
#
############################################################################################