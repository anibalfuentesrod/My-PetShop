from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from .models import Order, Product, Cart, CartItem, Category, ShippingAddress, OrderItem
from .forms import ShippingAddressForm
from django.views import View
import stripe
from django.conf import settings
from django.http import JsonResponse
from django.dispatch import receiver
from allauth.account.signals import user_logged_in
from allauth.socialaccount.models import SocialAccount
from .models import UserProfile
from django.http import Http404
import json

# Create your views here.
############################################################################################
# HOME Page
############################################################################################
def index(request):
    username = request.user
    products = Product.objects.filter(available=True)  # Adjust as needed
    return render(request, 'index.html', {
        'products': products,
        'username': request.user.username if request.user.is_authenticated else 'Guest',
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
    search_query = request.GET.get('search', '')
    category_id = request.GET.get('category', None)
    
    if category_id:
        products = Product.objects.filter(category_id=category_id)
    else:
        products = Product.objects.all()

    if search_query:
        products = products.filter(name__icontains=search_query)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        product_list = list(products.values('id', 'name', 'price', 'weight', 'image', 'category__name'))
        return JsonResponse({'products': product_list})

    context = {
        'products': products,
        'categories': categories,
        'selected_category': category_id,
        'search_query': search_query,
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
        # Check if the user has a shipping address
        try:
            shipping_address = ShippingAddress.objects.get(user=request.user)
        except ShippingAddress.DoesNotExist:
            return redirect('shipping_address')  # Redirect to shipping address form

        # Check if it's a single product or cart checkout
        product_id = kwargs.get('pk')
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
            line_items = [
                {
                    'price': item.product.stripe_price_id,
                    'quantity': item.quantity,
                } for item in cart_items
            ]

        # Prepare shipping options (You can add more options here as needed)
        shipping_options = [{
            'shipping_rate_data': {
                'type': 'fixed_amount',
                'fixed_amount': {'amount': 500, 'currency': 'usd'},
                'display_name': 'Standard shipping',
                'delivery_estimate': {
                    'minimum': {'unit': 'business_day', 'value': 5},
                    'maximum': {'unit': 'business_day', 'value': 7},
                },
            }
        }]

        # Allow a variety of countries, including the user's selected country
        allowed_countries = ['US', 'PR', 'CA', 'GB', 'MX', 'AU']  # Add other Stripe-supported countries
        user_country = shipping_address.country

        # Ensure that the user's country is included in allowed countries
        if user_country not in allowed_countries:
            allowed_countries.append(user_country)

        # Ensure that user has a valid email
        email = request.user.email
        if not email:
            # Fallback to user profile email if available
            try:
                user_profile = UserProfile.objects.get(user=request.user)
                email = user_profile.email
            except UserProfile.DoesNotExist:
                email = None

        if not email:
            return JsonResponse({'error': 'No valid email associated with user'}, status=400)

        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                shipping_address_collection={
                    'allowed_countries': allowed_countries,
                },
                shipping_options=shipping_options,
                customer_email=email,  # Use the verified email
                success_url=settings.YOUR_DOMAIN + '/success/',
                cancel_url=settings.YOUR_DOMAIN + '/cancel/',
            )
            return JsonResponse({'id': checkout_session.id})
        except Exception as e:
            # Log the error
            print(f"Stripe Checkout Session Error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)
############################################################################################
# Success Form si el pago fue exitoso
############################################################################################
def success_view(request):
    if not request.user.is_authenticated:
        return redirect('account_login')
    cart = Cart.objects.get(user=request.user)
    cart_items = cart.cartitem_set.all()

    # Create a new order
    order = Order.objects.create(
        customer=request.user,
        shipping_address=ShippingAddress.objects.get(user=request.user),
        total_price=cart.total_price(),  # Assuming this function exists in your cart model
        is_paid=True,  # Mark order as paid
    )

    # Add cart items to the order
    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.product.price
        )

    # Clear the cart after order is placed
    cart.cartitem_set.all().delete()

    return render(request, 'success.html', {'order': order})
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

    # Parse the quantity from the request body (default to 1 if not provided)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            quantity = int(data.get('quantity', 1))
        except (ValueError, KeyError, json.JSONDecodeError):
            return JsonResponse({"error": "Invalid quantity provided."}, status=400)

        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

        if created:
            cart_item.quantity = quantity  # Set the new quantity
        else:
            cart_item.quantity += quantity  # Increment the quantity if it exists

        cart_item.save()

        return JsonResponse({"message": f"{quantity} item(s) added to cart successfully."})
    return JsonResponse({"error": "Invalid request method."}, status=400)
############################################################################################
# This view displays the user's cart, including all items and the total price
############################################################################################
@login_required
def view_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.cartitem_set.all()
    total_price = cart.total_price()
    
    try:
        shipping_address = ShippingAddress.objects.get(user=request.user)
    except ShippingAddress.DoesNotExist:
        shipping_address = None

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'shipping_address': shipping_address,
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
# Funcion para añadir o editar el shipping address
############################################################################################
@login_required
def shipping_address_view(request):
    try:
        shipping_address = ShippingAddress.objects.get(user=request.user)
    except ShippingAddress.DoesNotExist:
        shipping_address = None

    if request.method == 'POST':
        form = ShippingAddressForm(request.POST, instance=shipping_address)
        if form.is_valid():
            shipping_address = form.save(commit=False)
            shipping_address.user = request.user
            shipping_address.save()
            return redirect('view_cart')
    else:
        form = ShippingAddressForm(instance=shipping_address)

    return render(request, 'shipping_address.html', {
        'form': form
    })
############################################################################################
# Funcion para foto de usuario NEW CODE
############################################################################################
@login_required
def user_profile_view(request):
    user = request.user
    # Check if the user is associated with a Google account
    social_account = SocialAccount.objects.filter(user=user, provider='google').first()
    # Retrieve the profile picture URL if available
    profile_picture_url = social_account.extra_data.get('picture') if social_account else None
    
    # Render the user profile template with the user data
    return render(request, 'user_profile.html', {
        'username': user.username,
        'email': user.email,
        'date_joined': user.date_joined,
        'profile_picture_url': profile_picture_url,
    })