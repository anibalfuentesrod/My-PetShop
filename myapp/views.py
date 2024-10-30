from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required
from .models import Order, Product, Cart, CartItem, Category, ShippingAddress, OrderItem, UserProfile
from .forms import ShippingAddressForm
from django.views import View
import stripe
from django.conf import settings
from django.http import JsonResponse
from django.dispatch import receiver
from allauth.account.signals import user_logged_in
from allauth.socialaccount.models import SocialAccount
from django.http import Http404
import json
from allauth.socialaccount.helpers import complete_social_login
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from .forms import CustomUserCreationForm
from django.core.mail import send_mail
from django.dispatch import receiver
from django.urls import reverse
from django.template.loader import render_to_string
from django.contrib.auth.models import User


# Home Page
def index(request):
    username = request.user
    products = Product.objects.filter(available=True)
    return render(request, 'index.html', {
        'products': products,
        'username': request.user.username if request.user.is_authenticated else 'Guest',
    })

# Register
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

# Login
# Login
def login_form(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        
        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)
            if user is not None:
                login(request, user)

                # Try to send a welcome email after a successful login
                try:
                    subject = 'Welcome to My-PetShop!'
                    product_link = request.build_absolute_uri(reverse('products'))

                    # Render the HTML email template
                    html_message = render_to_string('email.html', {
                        'username': user.username,
                        'product_link': product_link,
                    })

                    # Send the email
                    send_mail(
                        subject,
                        '',  # Leave the plain text version empty
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        fail_silently=False,
                        html_message=html_message  # Pass the rendered HTML message
                    )
                except Exception as e:
                    print(f"Failed to send welcome email: {e}")

                return redirect('index')
            else:
                return render(request, 'login.html', {'error': 'Invalid email or password'})
        except User.DoesNotExist:
            return render(request, 'login.html', {'error': 'Invalid email or password'})
    
    return render(request, 'login.html')

# Logout
def logout_form(request):
    logout(request)
    return redirect('index')

# User Profile
@login_required
def user_profile(request):
    user = request.user
    user_profile, created = UserProfile.objects.get_or_create(user=user)
    return render(request, 'user_profile.html', {
        'username': user.username,
        'email': user.email,
        'date_joined': user.date_joined,
    })


# Product Listing
def products(request):
    categories = Category.objects.all()
    search_query = request.GET.get('search', '').strip()
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

# Product Details
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'product_detail.html', {
        'product': product,
    })


# Checkout Session
stripe.api_key = settings.STRIPE_SECRET_KEY

class CreateCheckoutSessionView(View):
    def post(self, request, *args, **kwargs):
        # Check if the user has a shipping address
        try:
            shipping_address = ShippingAddress.objects.get(user=request.user)
        except ShippingAddress.DoesNotExist:
            return redirect('shipping_address')

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

        # Prepare shipping options (Cambia aqui el shipping cuanto cuesta y días)
        shipping_options = [{
            'shipping_rate_data': {
                'type': 'fixed_amount',
                'fixed_amount': {'amount': 500, 'currency': 'usd'},
                'display_name': 'Standard shipping',
                'delivery_estimate': {
                    'minimum': {'unit': 'business_day', 'value': 14},
                    'maximum': {'unit': 'business_day', 'value': 16},
                },
            }
        }]


        allowed_countries = ['US', 'PR', 'CA', 'GB', 'MX', 'AU']
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

# Succes Page
@login_required
def success_view(request):

    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        return redirect('view_cart')

    cart_items = cart.cartitem_set.all()

    # Crear una nueva orden
    order = Order.objects.create(
        customer=request.user,
        shipping_address=ShippingAddress.objects.get(user=request.user),
        total_price=cart.total_price(),
        is_paid=True,
    )

    # Añadir los artículos del carrito a la orden
    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.product.price
        )

    # Limpiar el carrito después de realizar el pedido
    cart.cartitem_set.all().delete()

    return render(request, 'success.html', {'order': order})

# Cancel Page
def cancel_view(request):
    return render(request, 'cancel.html')


# Signal to Save User Profile
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

# Add to cart
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


# View Cart
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

# Remove from cart product
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()

    return redirect('view_cart')


# Shipping view 
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

# CREATES NEW PROFILE
@receiver(user_logged_in)
def save_user_profile(sender, request, user, **kwargs):
    # Check if the user already has a profile, if not, create one
    user_profile, created = UserProfile.objects.get_or_create(user=user)
    
    # Optionally update email or other fields
    if request.user.email and not user_profile.email:
        user_profile.email = request.user.email  # Keep the email updated

    user_profile.save()


# Delete Profile
@login_required
def delete_account(request):
    user = request.user
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'Your account has been deleted successfully.')
        return redirect('index')
    return render(request, 'delete_account.html')

def contact(request):
    return render(request, 'contact.html')

def terms(request):
    return render(request, 'terms.html')

def privacy(request):
    return render(request, 'privacy.html')

def refund(request):
    return render(request, 'refund.html')

def shipping(request):
    return render(request, 'shipping.html')


def landing(request):
    return render(request, 'landing_page.html')