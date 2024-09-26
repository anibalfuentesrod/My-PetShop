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
    path('create-checkout-session/<int:pk>/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
]