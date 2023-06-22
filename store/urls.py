from django.urls import path
from . import views

urlpatterns = [
    path('', views.store, name="store"),
    path('cart/', views.cart, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('success/', views.checkout, name='payment-success'),

    path('update_item/', views.updateItem, name='update_item'),
    path('process_order/', views.process_order, name='process_order'),
]