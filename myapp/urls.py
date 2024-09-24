from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.login_form, name='login'),
    path('logout/', views.logout_form, name='logout'),
    path('profile/', views.user_profile, name='profile'),
    path('products/', views.products, name='products'),
    path('order/<int:product_id>/', views.product_detail, name='product_detail'),
    path('success/', views.success_view, name='success'),
    path('cancel/', views.cancel_view, name='cancel')
]