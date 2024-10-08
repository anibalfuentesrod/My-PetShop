from django.urls import path
from . import views
from .views import CreateCheckoutSessionView

urlpatterns = [
    path('', views.index, name='index'),
    path('logout/', views.logout_form, name='logout'),
    path('profile/', views.user_profile, name='profile'),
    path('products/', views.products, name='products'),
    path('products/<int:product_id>/', views.product_detail, name='product_detail'),
    path('success/', views.success_view, name='success'),
    path('cancel/', views.cancel_view, name='cancel'),
    path('create-checkout-session/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('create-checkout-session/<int:pk>/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('shipping-address/', views.shipping_address_view, name='shipping_address'),
    # NEW CODE
    path('profile/', views.user_profile_view, name='profile'),
]