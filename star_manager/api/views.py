from django.contrib.auth.models import Group, User
from django.http import JsonResponse
from rest_framework import permissions, viewsets

from api import serializers
from star_manager.settings import sdb


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = serializers.UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all().order_by('name')
    serializer_class = serializers.GroupSerializer
    permission_classes = [permissions.IsAuthenticated]


class AllChatsView(viewsets.ViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    def getresponse(self, *args, **kwargs):
        if 'user_id' not in self.kwargs:
            with sdb.syncpool().connection() as conn:
                with conn.cursor() as c:
                    chats = c.execute('select chat_id from allchats where chat_id>0').fetchall()
        else:
            with sdb.syncpool().connection() as conn:
                with conn.cursor() as c:
                    chats = c.execute('select chat_id from allchats where chat_id>0 and chat_id=ANY(%s)',
                                      ([i[0] for i in c.execute('select chat_id from accesslvl where uid=%s',
                                                                (self.kwargs['user_id'],)).fetchall()],)).fetchall()
        data = {"status": True, "response": [i[0] for i in chats]}
        return JsonResponse(data)


class AccessLvlView(viewsets.ViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    def getresponse(self, *args, **kwargs):
        data = {"status": False, "error": 404}
        if 'user_id' in self.kwargs:
            with sdb.syncpool().connection() as conn:
                with conn.cursor() as c:
                    ac = c.execute('select access_level from accesslvl where chat_id=%s and uid=%s',
                                   (self.kwargs['chat_id'], self.kwargs['user_id'],)).fetchone()
            if ac is not None:
                data = {"status": True, "response": ac[0]}
        else:
            with sdb.syncpool().connection() as conn:
                with conn.cursor() as c:
                    ac = c.execute('select uid, access_level from accesslvl where chat_id=%s and uid>0',
                                   (self.kwargs['chat_id'],)).fetchall()
            if len(ac) != 0:
                data = {"status": True, "response": {f"{i[0]}": i[1] for i in ac}}
        return JsonResponse(data)


def handler404():
    return JsonResponse({'error': 'method not found'})
