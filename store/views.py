from django.shortcuts import render, redirect, HttpResponseRedirect
from django.http import JsonResponse
import json
import datetime
import stripe
from django.conf import settings
from .models import *
from .utils import cookie_cart, cart_data, guest_order

stripe.api_key = settings.STRIPE_SECRET_KEY

def store(request):

    data = cart_data(request)
    cart_items = data['cart_items']

    products = Product.objects.all()
    context = {'products': products, 'cart_items': cart_items,}
    return render(request, 'store/store.html', context)


def cart(request):

    data = cart_data(request)
    cart_items = data['cart_items']
    order = data['order']
    items = data['items']

    context = {'items':items, 'order':order,'cart_items':cart_items,}
    return render(request, 'store/cart.html', context)


def checkout(request):



    if request.method == 'POST':
        YOUR_DOMAIN = 'http://127.0.0.1:8000'
        try:
            checkout_session = stripe.checkout.Session.create(
                line_items=[
                    {
                        # Provide the exact Price ID (for example, pr_1234) of the product you want to sell
                        'price': '2',
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url=YOUR_DOMAIN + '/success',
                cancel_url=YOUR_DOMAIN + '/cancel',
            )
            print(checkout_session)
        except Exception as e:
            print("Here",e)
        
        return HttpResponseRedirect("/")
    data = cart_data(request)
    cart_items = data['cart_items']
    order = data['order']
    items = data['items']

    context = {'items':items, 'order':order,'cart_items': cart_items,}
    return render(request, 'store/checkout.html', context)

def updateItem(request):
    data = json.loads(request.body)
    product_id = data['productId']
    action = data['action']
    print('action',action)
    print('productId:', product_id)

    customer = request.user.customer
    product = Product.objects.get(id=product_id)
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)
    
    if action == 'add':
        orderItem.quantity = (orderItem.quantity + 1 )
    elif action == 'remove':
        orderItem.quantity = (orderItem.quantity - 1)
    
    orderItem.save()

    if orderItem.quantity <= 0:
        orderItem.delete()

    return JsonResponse('Item was added', safe=False)

from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def process_order(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)

    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, complete=False)


    else:
        customer, order = guest_order(request, data)
    
    total = float(data['form']['total'])
    order.transaction_id = transaction_id

    if total == float(order.get_cart_total):
        order.complete = True
    
    order.save()

    if order.shipping == True:
        ShippingAddress.objects.create(
                customer=customer,
                order=order,
                address=data['shipping']['address'],
                city=data['shipping']['city'],
                state=data['shipping']['state'],
                zipcode=data['shipping']['zipcode'],
        )
    
    return JsonResponse('Payment Complete', safe=False)
    
#Error Pages

def handling_404(request,exception):
    return render(request, 'error_pages/404.html')

def handling_500(request):
    return render(request, 'store/error_pages/500.html')