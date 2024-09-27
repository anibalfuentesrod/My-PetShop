from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, logout
from django.contrib.auth.decorators import login_required
from .models import Order, Product, Cart, CartItem, Category
from django.views import View
import stripe
from django.conf import settings
from django.http import JsonResponse
from django.dispatch import receiver
from allauth.account.signals import user_logged_in
from .models import UserProfile
from django.http import Http404

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
# Cerrar la Sesión
############################################################################################
def logout_form(request):
    logout(request)
    return redirect('index')
############################################################################################
# Vista Protegida: Dashboard del Usuario
############################################################################################
@login_required
def user_profile(request):
    user = request.user
    try:
        user_profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        raise Http404("UserProfile does not exist for this user.")
    
    return render(request, 'user_profile.html', {
        'username': user.username,
        'email': user_profile.email,
        'date_joined': user.date_joined,
    })
############################################################################################
# Todos los productos
############################################################################################
def products(request):
    categories = Category.objects.all()
    
    category_id = request.GET.get('category', None)
    
    if category_id:
        products = Product.objects.filter(category_id=category_id)
    else:
        products = Product.objects.all()

    context = {
        'products': products,
        'categories': categories,
        'selected_category': category_id
    }
    return render(request, 'products.html', context)
############################################################################################
# Los detalles de los productos
############################################################################################
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'product_detail.html', {
        'product': product,
    })
############################################################################################
# Checkout Session Let's goo
############################################################################################
stripe.api_key = settings.STRIPE_SECRET_KEY

class CreateCheckoutSessionView(View):
    def post(self, request, *args, **kwargs):
        # Check if the request is for a single product or cart checkout
        product_id = kwargs.get('pk')  # Get the product ID from the URL if present
        if product_id:
            # Single product checkout
            product = get_object_or_404(Product, id=product_id)

            line_items = [{
                'price': product.stripe_price_id,
                'quantity': 1,
            }]
        else:
            # Cart checkout
            cart = Cart.objects.get(user=request.user)
            cart_items = cart.cartitem_set.all()

            line_items = []
            for item in cart_items:
                line_items.append({
                    'price': item.product.stripe_price_id,
                    'quantity': item.quantity,
                })

        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=settings.YOUR_DOMAIN + '/success/',
                cancel_url=settings.YOUR_DOMAIN + '/cancel/',
            )
            return JsonResponse({'id': checkout_session.id})
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
@receiver(user_logged_in)
def save_user_profile(sender, request, user, **kwargs):
    google_account = user.socialaccount_set.filter(provider='google').first()
    if google_account:
        extra_data = google_account.extra_data
        profile_image = extra_data.get('picture', '')
        email = extra_data.get('email', '')
        if not email:
            print("Email not found in extra_data")

        UserProfile.objects.update_or_create(
            user=user,
            defaults={
                'profile_image': profile_image,
                'google_id': google_account.uid,
                'email': email,
            }
        )
############################################################################################
# When user adds item to cart
############################################################################################
@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    cart, created = Cart.objects.get_or_create(user=request.user)

    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if not created:
        # if item already exists, increa it's quantity
        cart_item.quantity += 1
        cart_item.save()

    return redirect('view_cart')
############################################################################################
# This view displays the user's cart, including all items and the total price
############################################################################################
@login_required
def view_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.cartitem_set.all()
    total_price = cart.total_price()

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
    }

    return render(request, 'view_cart.html', context)
############################################################################################
# remove item from cart view
############################################################################################
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()

    return redirect('view_cart')
############################################################################################