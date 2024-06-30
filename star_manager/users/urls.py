from django.urls import path, include

from users import views

app_name = 'users'

urlpatterns = [
    path('login/', views.login_user, name='login'),
    path('login', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('lk/', views.lk, name='lk'),
    path('', views.lk, name='home'),
]
