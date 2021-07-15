# ad, asdfasdf
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse

from django.contrib.auth.forms import UserCreationForm
from .forms import CreateUserForm, ReviewForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from .decorators import unauthenticated_user

import json
import datetime

from .models import * 
from .utils import cookieCart, cartData, guestOrder

def store(request):

	data = cartData(request)
	cartItems = data['cartItems']
	
	products = Product.objects.all()
	context = {'products':products, 'cartItems':cartItems}
	return render(request, 'store/store.html', context)

def view_product(request, pk):
	
	data = cartData(request)
	cartItems = data['cartItems']
	product = Product.objects.get(id=pk)
	user = request.user
	
	reviews = Review.objects.all()

	context = {'product':product, 'cartItems':cartItems, 'reviews':reviews}
	
	# if request.method == 'POST':
	# 	form = ReviewForm(request.POST)
	# 	if form.is_valid():
	# 		Review.objects.create(
	# 			customer=user.customer,
	# 			product=product,
	# 			review=form.cleaned_data.get('review'),
	# 			rating=form.cleaned_data.get('rating'),
	# 			)
	# 		return redirect('/')

	# else:
	# 	form = ReviewForm()
	# 	context['form'] = form;

	# context['form'] = ReviewForm()
	
	return render(request, 'store/view_product.html', context)

def cart(request):

	data = cartData(request)
	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	context = {'items':items, 'order':order, 'cartItems':cartItems}
	return render(request, 'store/cart.html', context)

def checkout(request):
	
	data = cartData(request)
	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	context = {'items':items, 'order':order, 'cartItems':cartItems, 'shipping':False}
	return render(request, 'store/checkout.html', context)

def updateItem(request):
	data = json.loads(request.body)
	productId = data['productId']
	action = data['action']

	print('Action is ', action)
	print('productId is', productId)

	customer = request.user.customer
	product = Product.objects.get(id=productId)
	order, created = Order.objects.get_or_create(customer=customer, complete=False)

	orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

	if action == 'add':
		orderItem.quantity = (orderItem.quantity + 1)
	elif action == 'remove':
		orderItem.quantity = (orderItem.quantity - 1)
	
	orderItem.save()
	if orderItem.quantity <= 0:
		orderItem.delete()
		
	return JsonResponse('Item was added', safe=False)

def processOrder(request):
	transaction_id = datetime.datetime.now().timestamp()
	data = json.loads(request.body)

	if request.user.is_authenticated:
		customer = request.user.customer
		order, created = Order.objects.get_or_create(customer=customer, complete=False)

	else:
		customer, order = guestOrder(request, data)

	total = float(data['form']['total'])
	order.transaction_id = transaction_id

	if total == order.get_cart_total:
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

	return JsonResponse('Payment Complete!!!', safe=False)


@unauthenticated_user
def registerPage(request):
	
	form = CreateUserForm()
	if request.method == 'POST':
		form = CreateUserForm(request.POST)
		if form.is_valid():
			user = form.save()
			username = form.cleaned_data.get('username')

			Customer.objects.create(
				user=user,
				name=user.username,
				email=user.email,
				)
			messages.success(request, 'Account was created successfully for ' + username)
			
			return redirect('login')

	context = {'form' : form}
	return render(request, 'store/register.html', context)


@unauthenticated_user
def loginPage(request):
	
	if request.method == 'POST':
		username = request.POST.get('username')
		password = request.POST.get('password')
		
		user = authenticate(request, username=username, password=password)

		if user is not None:
			login(request, user)
			return redirect('store')
		else:
			messages.info(request, 'Username or Password is incorrect')
			
	context = {}
	return render(request, 'store/login.html', context)


def logoutUser(request):
	logout(request)
	return redirect('store')

