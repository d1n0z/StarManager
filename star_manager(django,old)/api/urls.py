from django.urls import include, path
from rest_framework import routers

from api import views

app_name = 'api'

router = routers.DefaultRouter()
# router.register(r'api-users', views.UserViewSet)
# router.register(r'api-groups', views.GroupViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
action = {'get': 'getresponse'}
urlpatterns = [
    path('', include(router.urls)),
    path('v1/allchats', views.AllChatsView.as_view(action), name='allchats'),
    path('v1/allchats/<int:user_id>', views.AllChatsView.as_view(action), name='allchats'),
    path('v1/getaccesslvl/<int:chat_id>', views.AccessLvlView.as_view(action), name='allchats'),
    path('v1/getaccesslvl/<int:chat_id>/<int:user_id>', views.AccessLvlView.as_view(action), name='allchats'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]

handler404 = views.handler404
