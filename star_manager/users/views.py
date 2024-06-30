from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse

from config.config import data

from .forms import LoginUserForm


app_name = "users"
data |= {
    'profile': ''
}


def login_user(request):
    if request.method == 'GET':
        form = LoginUserForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(request, uid=cd['uid'])
            if user and user.is_active:
                login(request, user)
                return render(request, '/home', data | {'name': 'Ihuha D1n0', 'avatar': '123'})
    return redirect('/login/vk-oauth2/', permanent=True)


@login_required(login_url='/users/login')
def logout_user(request):
    logout(request)
    return redirect("/")


@login_required(login_url='/users/login')
def lk(request):
    return render(request, 'users/lk.html', data)
