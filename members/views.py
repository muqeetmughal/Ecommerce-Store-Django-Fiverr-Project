from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import RegisterUserForm
from django.contrib.auth.forms import UserCreationForm

def login_user(request):
    if request.method == 'POST':
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
                login(request, user)
                return redirect('store')
            
        else:
            messages.success(request, ('There was an error logging you in, try again.'))
            return redirect('login')

    else:
        return render(request, 'registration/login.html', {})

def logout_user(request):
    logout(request)
    messages.success(request, ('You Were Logged Out '))

    return redirect('store')

def register_user(request):
    if request.method == 'POST':
        form = RegisterUserForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, ('Registration Successful'))
            return redirect('store')
    else:
        form = RegisterUserForm()

    return render(request,'registration/register.html', {'form':form} )