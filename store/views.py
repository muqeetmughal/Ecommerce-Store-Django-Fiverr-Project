from django.shortcuts import render, redirect, HttpResponseRedirect
from django.http import JsonResponse
import json
import datetime
import stripe
from django.conf import settings
from .models import *
from .utils import cookie_cart, cart_data, guest_order
from django.views.generic.base import TemplateView
from django.http.response import JsonResponse, HttpResponse


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


def create_checkout_session(items, order_id):
    YOUR_DOMAIN = 'http://127.0.0.1:8000/'
    line_items = []
    checkout_session = None
    for item in items:
        print(type(item))
        product = item.product
        # convert product to dictionary
        product = product.__dict__
        line_items.append({
            'price_data': {
                'currency': 'usd',
                'unit_amount': int(product['price'] * 100),
                'product_data': {
                    'name': product['name'],
                    'images': [YOUR_DOMAIN + product['image']],
                },
            },
            'quantity': item.quantity,
        })
    try:
        # we create session without stripe_price_id
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='payment',
            success_url=YOUR_DOMAIN + '/success',
            cancel_url=YOUR_DOMAIN + '/cancel',
            line_items=line_items,
            metadata={
                'order_id': order_id
            }
        )
        print(checkout_session)
    except Exception as e:
        print("Here",e)

    return checkout_session


def checkout(request):

    # get the items from session
    data = cart_data(request)
    cart_items = data['cart_items']
    order = data['order']
    items = data['items']

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
        checkout_session = create_checkout_session(items, order.id)
        return redirect(checkout_session.url)


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

class SuccessView(TemplateView):
    template_name = 'store/success.html'


class CancelledView(TemplateView):
    template_name = 'store/cancelled.html'



@csrf_exempt
def stripe_webhook(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    endpoint_secret = settings.STRIPE_ENDPOINT_SECRET
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        print("Payment was successful.")
        order = Order.objects.get(id=event['data']['object']['metadata']['order_id'])
        order.complete = True
        order.transaction_id = event['data']['object']['payment_intent']
        order.save()

    return HttpResponse(status=200)
