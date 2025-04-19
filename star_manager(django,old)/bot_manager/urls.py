from django.urls import path, include

from bot_manager import views

urlpatterns = [
    path('', include('social_django.urls')),
    path('users/', include('users.urls', namespace='users')),
    path('', views.index, name='index'),
    path('chats/', views.chats, name='chats'),
    path('home/', views.index, name='home'),
    path('privacy/', views.privacy, name='privacy'),
    path('buy/', views.buy, name='buy'),
    path('yookassa/', views.yookassa, name='yookassa'),
]

handler404 = views.handler404
